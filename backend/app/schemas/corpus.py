from typing import Literal

from pydantic import BaseModel, Field

SourceId = Literal[
    "gdpr",
    "edpb_consent_05_2020",
    "edpb_breach_09_2022",
    "edpb_access_01_2022",
]
DocType = Literal["regulation_article", "regulation_recital", "guideline_section"]


class Chunk(BaseModel):
    chunk_id: str = Field(..., examples=["gdpr:art33:p1"])
    source_id: SourceId
    doc_type: DocType
    instrument: str = Field(..., examples=["Regulation (EU) 2016/679 (GDPR)"])
    jurisdiction: Literal["EU"] = "EU"
    effective_date: str = Field(..., examples=["2018-05-25"])
    version_date: str = Field(..., examples=["2016-05-04"])
    chapter: str | None = None
    chapter_title: str | None = None
    section: str | None = None
    article: int | None = None
    article_title: str | None = None
    paragraph: int | None = None
    recital: int | None = None
    guideline_section: str | None = None
    citation_label: str = Field(..., examples=["GDPR Art. 33(1)"])
    breadcrumb: str = Field(..., examples=["GDPR > Chapter IV > Section 2 > Article 33 > (1)"])
    url: str = Field(..., examples=["https://eur-lex.europa.eu/eli/reg/2016/679/oj#art_33"])
    display_text: str
    embed_text: str
    token_count: int
    content_hash: str
