from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TypeVar

import openai
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from .models import (
    BrandCandidate,
    BrandGenerationResult,
    FinalBrandResult,
    MarketingReview,
    MarketingReviewResult,
    VCReview,
    VCReviewResult,
)


# A projekt gyökérmappája:
# TicketPilot/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# A promptfájlok helye:
# TicketPilot/tools/brand_finder/prompts/
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

# Alapértelmezett modell.
# A backend/.env fájlban OPENAI_MODEL értékkel felülírható.
DEFAULT_MODEL = "gpt-5.5"

T = TypeVar("T", bound=BaseModel)


class BrandFinderAIService:
    """
    A Brand Finder AI-folyamat OpenAI-rétege.

    Folyamat:
    1. Branding Expert létrehozza a neveket.
    2. VC Investor értékeli és szűri őket.
    3. Marketing Director újraértékeli a VC által elfogadott neveket.
    4. A rendszer összefésüli az eredményeket.
    """

    def __init__(
        self,
        client: OpenAI | None = None,
        model: str | None = None,
    ) -> None:
        self._load_environment()

        api_key = os.getenv("OPENAI_API_KEY")

        if client is None and not api_key:
            raise RuntimeError(
                "Az OPENAI_API_KEY nem található.\n"
                "Add hozzá a backend/.env fájlhoz:\n"
                "OPENAI_API_KEY=sk-..."
            )

        self.client = client or OpenAI(
            api_key=api_key,
            timeout=180.0,
            max_retries=3,
        )

        self.model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

        self.branding_prompt = self._load_prompt("branding_expert.txt")
        self.vc_prompt = self._load_prompt("vc_investor.txt")
        self.marketing_prompt = self._load_prompt(
            "marketing_director.txt"
        )

    @staticmethod
    def _load_environment() -> None:
        """
        Betölti a környezeti változókat.

        Elsőként a backend/.env fájlt keresi, mert a TicketPilot
        jelenlegi API-kulcsa várhatóan ott található.

        Ezután a projekt gyökerében található .env fájlt is megpróbálja
        betölteni, de nem írja felül a már betöltött értékeket.
        """
        backend_env = PROJECT_ROOT / "backend" / ".env"
        root_env = PROJECT_ROOT / ".env"

        if backend_env.exists():
            load_dotenv(backend_env, override=False)

        if root_env.exists():
            load_dotenv(root_env, override=False)

    @staticmethod
    def _load_prompt(filename: str) -> str:
        """
        Beolvassa és ellenőrzi a megadott promptfájlt.
        """
        prompt_path = PROMPTS_DIR / filename

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"A promptfájl nem található: {prompt_path}"
            )

        prompt = prompt_path.read_text(encoding="utf-8").strip()

        if not prompt:
            raise ValueError(
                f"A promptfájl üres: {prompt_path}"
            )

        return prompt

    def _request_structured_output(
        self,
        *,
        instructions: str,
        user_input: str,
        output_model: type[T],
        operation_name: str,
    ) -> T:
        """
        Strukturált OpenAI-választ kér egy Pydantic-modell szerint.

        A Responses API parse funkciója közvetlenül a megadott
        Pydantic-modellbe alakítja a választ.
        """
        try:
            response = self.client.responses.parse(
                model=self.model,
                instructions=instructions,
                input=[
                    {
                        "role": "user",
                        "content": user_input,
                    }
                ],
                text_format=output_model,
            )

        except openai.AuthenticationError as exc:
            raise RuntimeError(
                "Az OpenAI API-kulcs hibás vagy nem érvényes."
            ) from exc

        except openai.RateLimitError as exc:
            raise RuntimeError(
                "Az OpenAI API elérte az ideiglenes használati "
                "vagy sebességi korlátot. Próbáld újra később."
            ) from exc

        except openai.APITimeoutError as exc:
            raise RuntimeError(
                f"Időtúllépés történt ennél a lépésnél: "
                f"{operation_name}"
            ) from exc

        except openai.APIConnectionError as exc:
            raise RuntimeError(
                "Nem sikerült kapcsolódni az OpenAI API-hoz. "
                "Ellenőrizd az internetkapcsolatot."
            ) from exc

        except openai.APIStatusError as exc:
            request_id = getattr(exc, "request_id", None)
            request_info = (
                f" Request ID: {request_id}"
                if request_id
                else ""
            )

            raise RuntimeError(
                f"Az OpenAI API hibát adott a(z) "
                f"'{operation_name}' lépésnél. "
                f"HTTP-státusz: {exc.status_code}."
                f"{request_info}"
            ) from exc

        except openai.APIError as exc:
            raise RuntimeError(
                f"OpenAI API-hiba történt a(z) "
                f"'{operation_name}' lépésnél."
            ) from exc

        parsed = response.output_parsed

        if parsed is None:
            refusal = self._extract_refusal(response)

            if refusal:
                raise RuntimeError(
                    f"Az AI nem teljesítette a(z) "
                    f"'{operation_name}' kérést: {refusal}"
                )

            raise RuntimeError(
                f"A(z) '{operation_name}' lépés nem adott "
                "érvényes strukturált választ."
            )

        return parsed

    @staticmethod
    def _extract_refusal(response: object) -> str | None:
        """
        Megpróbálja kiolvasni az esetleges modell-visszautasítást.

        A getattr használata miatt akkor sem omlik össze,
        ha az SDK válaszobjektuma később némileg változik.
        """
        output_items = getattr(response, "output", None)

        if not output_items:
            return None

        for output_item in output_items:
            contents = getattr(output_item, "content", None)

            if not contents:
                continue

            for content in contents:
                refusal = getattr(content, "refusal", None)

                if refusal:
                    return str(refusal)

        return None

    def generate_candidates(self) -> BrandGenerationResult:
        """
        A Branding Expert pontosan 10 prémium márkanevet generál.
        """
        print(
            "\n[1/3] Branding Expert: "
            "prémium márkanevek generálása...",
            flush=True,
        )

        user_input = (
            "Create the premium naming proposal now.\n\n"
            "Return exactly 10 distinct candidates.\n"
            "Follow every requirement from your instructions.\n"
            "Do not include the reference names themselves."
        )

        result = self._request_structured_output(
            instructions=self.branding_prompt,
            user_input=user_input,
            output_model=BrandGenerationResult,
            operation_name="Branding Expert",
        )

        result.candidates = self._deduplicate_candidates(
            result.candidates
        )

        if not result.candidates:
            raise RuntimeError(
                "A Branding Expert nem generált használható nevet."
            )

        print(
            f"      Elkészült: {len(result.candidates)} "
            "egyedi név.",
            flush=True,
        )

        return result

    def review_with_vc(
        self,
        candidates: list[BrandCandidate],
    ) -> VCReviewResult:
        """
        A VC Investor értékeli az összes generált nevet.
        """
        if not candidates:
            raise ValueError(
                "A VC-értékeléshez nincs egyetlen jelölt sem."
            )

        print(
            "\n[2/3] VC Investor: "
            "jelöltek üzleti értékelése...",
            flush=True,
        )

        candidate_payload = [
            {
                "name": candidate.name,
                "pronunciation": candidate.pronunciation,
                "meaning": candidate.meaning,
                "brand_story": candidate.brand_story,
                "tagline": candidate.tagline,
                "target_positioning": (
                    candidate.target_positioning
                ),
            }
            for candidate in candidates
        ]

        user_input = (
            "Review every candidate in the JSON list below.\n\n"
            "Important requirements:\n"
            "- Return exactly one review for every submitted name.\n"
            "- Preserve every candidate name exactly.\n"
            "- Do not add new names.\n"
            "- Do not omit weak names; reject them explicitly.\n\n"
            f"Candidates:\n"
            f"{json.dumps(candidate_payload, indent=2, ensure_ascii=False)}"
        )

        result = self._request_structured_output(
            instructions=self.vc_prompt,
            user_input=user_input,
            output_model=VCReviewResult,
            operation_name="VC Investor",
        )

        result.reviews = self._normalize_vc_reviews(
            candidates=candidates,
            reviews=result.reviews,
        )

        approved_count = sum(
            review.approved for review in result.reviews
        )

        print(
            f"      Elfogadva: {approved_count}/"
            f"{len(result.reviews)} név.",
            flush=True,
        )

        return result

    def review_with_marketing(
        self,
        candidates: list[BrandCandidate],
        vc_reviews: list[VCReview],
    ) -> MarketingReviewResult:
        """
        A Marketing Director kizárólag a VC által elfogadott
        neveket értékeli tovább.
        """
        candidate_map = {
            self._name_key(candidate.name): candidate
            for candidate in candidates
        }

        approved_names = {
            self._name_key(review.name)
            for review in vc_reviews
            if review.approved
        }

        approved_candidates = [
            candidate_map[name_key]
            for name_key in approved_names
            if name_key in candidate_map
        ]

        if not approved_candidates:
            print(
                "\n[3/3] Marketing Director: "
                "nincs VC által elfogadott név.",
                flush=True,
            )
            return MarketingReviewResult(reviews=[])

        print(
            "\n[3/3] Marketing Director: "
            "márkaértékelés...",
            flush=True,
        )

        candidate_payload = [
            {
                "name": candidate.name,
                "pronunciation": candidate.pronunciation,
                "meaning": candidate.meaning,
                "brand_story": candidate.brand_story,
                "tagline": candidate.tagline,
                "logo_idea": candidate.logo_idea,
                "target_positioning": (
                    candidate.target_positioning
                ),
            }
            for candidate in approved_candidates
        ]

        user_input = (
            "Evaluate every candidate in the JSON list below.\n\n"
            "Important requirements:\n"
            "- Return exactly one review for every submitted name.\n"
            "- Preserve every candidate name exactly.\n"
            "- Do not add, rename, or omit candidates.\n"
            "- Apply the scoring thresholds strictly.\n\n"
            f"Candidates:\n"
            f"{json.dumps(candidate_payload, indent=2, ensure_ascii=False)}"
        )

        result = self._request_structured_output(
            instructions=self.marketing_prompt,
            user_input=user_input,
            output_model=MarketingReviewResult,
            operation_name="Marketing Director",
        )

        result.reviews = self._normalize_marketing_reviews(
            candidates=approved_candidates,
            reviews=result.reviews,
        )

        approved_count = sum(
            review.approved for review in result.reviews
        )

        print(
            f"      Elfogadva: {approved_count}/"
            f"{len(result.reviews)} név.",
            flush=True,
        )

        return result

    def run_ai_workflow(
        self,
    ) -> tuple[
        BrandGenerationResult,
        VCReviewResult,
        MarketingReviewResult,
        list[FinalBrandResult],
    ]:
        """
        Lefuttatja a teljes háromlépcsős AI-folyamatot.
        """
        generation_result = self.generate_candidates()

        vc_result = self.review_with_vc(
            generation_result.candidates
        )

        marketing_result = self.review_with_marketing(
            candidates=generation_result.candidates,
            vc_reviews=vc_result.reviews,
        )

        final_results = self.merge_results(
            candidates=generation_result.candidates,
            vc_reviews=vc_result.reviews,
            marketing_reviews=marketing_result.reviews,
        )

        return (
            generation_result,
            vc_result,
            marketing_result,
            final_results,
        )

    @staticmethod
    def merge_results(
        candidates: list[BrandCandidate],
        vc_reviews: list[VCReview],
        marketing_reviews: list[MarketingReview],
    ) -> list[FinalBrandResult]:
        """
        Összekapcsolja a három AI-szerep eredményeit.

        Csak azok a nevek kerülnek a döntőbe, amelyeket:
        - a VC Investor elfogadott;
        - a Marketing Director is elfogadott.
        """
        vc_map = {
            BrandFinderAIService._name_key(review.name): review
            for review in vc_reviews
        }

        marketing_map = {
            BrandFinderAIService._name_key(review.name): review
            for review in marketing_reviews
        }

        final_results: list[FinalBrandResult] = []

        for candidate in candidates:
            name_key = BrandFinderAIService._name_key(
                candidate.name
            )

            vc_review = vc_map.get(name_key)
            marketing_review = marketing_map.get(name_key)

            if vc_review is None or marketing_review is None:
                continue

            if not vc_review.approved:
                continue

            if not marketing_review.approved:
                continue

            final_score = BrandFinderAIService._calculate_final_score(
                vc_review=vc_review,
                marketing_review=marketing_review,
            )

            final_results.append(
                FinalBrandResult(
                    name=candidate.name,
                    pronunciation=candidate.pronunciation,
                    meaning=candidate.meaning,
                    brand_story=candidate.brand_story,
                    tagline=candidate.tagline,
                    logo_idea=candidate.logo_idea,
                    target_positioning=(
                        candidate.target_positioning
                    ),
                    vc_score=vc_review.score,
                    vc_reasoning=vc_review.reasoning,
                    vc_main_risk=vc_review.main_risk,
                    memorability_score=(
                        marketing_review.memorability_score
                    ),
                    enterprise_score=(
                        marketing_review.enterprise_score
                    ),
                    international_score=(
                        marketing_review.international_score
                    ),
                    differentiation_score=(
                        marketing_review.differentiation_score
                    ),
                    final_score=final_score,
                )
            )

        final_results.sort(
            key=lambda item: item.final_score,
            reverse=True,
        )

        return final_results

    @staticmethod
    def _calculate_final_score(
        *,
        vc_review: VCReview,
        marketing_review: MarketingReview,
    ) -> float:
        """
        Súlyozott végső pontszám.

        Súlyok:
        - VC hitelesség: 30%
        - megjegyezhetőség: 20%
        - enterprise hatás: 20%
        - nemzetközi használhatóság: 15%
        - megkülönböztethetőség: 15%
        """
        score = (
            vc_review.score * 0.30
            + marketing_review.memorability_score * 0.20
            + marketing_review.enterprise_score * 0.20
            + marketing_review.international_score * 0.15
            + marketing_review.differentiation_score * 0.15
        )

        return round(score, 2)

    @staticmethod
    def _deduplicate_candidates(
        candidates: list[BrandCandidate],
    ) -> list[BrandCandidate]:
        """
        Eltávolítja az ismétlődő és nyilvánvalóan hibás neveket.
        """
        unique_candidates: list[BrandCandidate] = []
        seen_names: set[str] = set()

        for candidate in candidates:
            cleaned_name = candidate.name.strip()

            if not cleaned_name:
                continue

            if not cleaned_name.isalpha():
                continue

            name_key = BrandFinderAIService._name_key(
                cleaned_name
            )

            if name_key in seen_names:
                continue

            candidate.name = cleaned_name
            seen_names.add(name_key)
            unique_candidates.append(candidate)

        return unique_candidates

    @staticmethod
    def _normalize_vc_reviews(
        *,
        candidates: list[BrandCandidate],
        reviews: list[VCReview],
    ) -> list[VCReview]:
        """
        Megtartja a jelöltekhez tartozó első VC-értékelést,
        és helyreállítja a név eredeti írásmódját.
        """
        candidate_names = {
            BrandFinderAIService._name_key(candidate.name):
                candidate.name
            for candidate in candidates
        }

        normalized: list[VCReview] = []
        seen_names: set[str] = set()

        for review in reviews:
            name_key = BrandFinderAIService._name_key(
                review.name
            )

            if name_key not in candidate_names:
                continue

            if name_key in seen_names:
                continue

            review.name = candidate_names[name_key]

            # A prompt szabályát programból is kikényszerítjük.
            if review.score < 80:
                review.approved = False

            normalized.append(review)
            seen_names.add(name_key)

        return normalized

    @staticmethod
    def _normalize_marketing_reviews(
        *,
        candidates: list[BrandCandidate],
        reviews: list[MarketingReview],
    ) -> list[MarketingReview]:
        """
        Megtartja a jelöltekhez tartozó első marketingértékelést,
        és a Python-oldalon is kikényszeríti a küszöböket.
        """
        candidate_names = {
            BrandFinderAIService._name_key(candidate.name):
                candidate.name
            for candidate in candidates
        }

        normalized: list[MarketingReview] = []
        seen_names: set[str] = set()

        for review in reviews:
            name_key = BrandFinderAIService._name_key(
                review.name
            )

            if name_key not in candidate_names:
                continue

            if name_key in seen_names:
                continue

            review.name = candidate_names[name_key]

            scores = [
                review.memorability_score,
                review.enterprise_score,
                review.international_score,
                review.differentiation_score,
            ]

            average_score = sum(scores) / len(scores)

            # A marketing prompt feltételeit Pythonban is ellenőrizzük.
            if min(scores) < 75 or average_score < 82:
                review.approved = False

            normalized.append(review)
            seen_names.add(name_key)

        return normalized

    @staticmethod
    def _name_key(name: str) -> str:
        """
        Egységes kulcs nevek összehasonlításához.
        """
        return name.strip().casefold()