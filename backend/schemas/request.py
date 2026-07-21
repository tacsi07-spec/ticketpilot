from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    name: str
    product: str
    market: str = (
        "Germany, European Union and "
        "international B2B market"
    )