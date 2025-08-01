# models.py
from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Literal, Dict, Any

Base = declarative_base()

# SQLAlchemy Model
class QAPair(Base):
    __tablename__ = 'qa_pairs'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    user_type = Column(String, nullable=False)
    client_id = Column(String,default=None)
    EOR_id = Column(String,default=None)
    contrator_id = Column(String,default=None)




# Common Metadata
class MetaField(BaseModel):
    user_type: str
    doc_id: Optional[str] = None
    EOR_id: Optional[str] = None
    client_id: Optional[str] = None
    contrator_id : Optional[str] = None

    # @model_validator(mode="after")
    # def validate_ids(self) -> 'MetaField':
    #     if not any([self.EOR_id, self.client_id, self.contrator_id]):
    #         raise ValueError("At least one of 'EOR_id', 'client_id', or 'contrator_id' must be provided.")
    #     return self

# InputData for ingestion
class InputData(BaseModel):
    metafield: MetaField
    data: Optional[List[Dict[str, Any]]] = None
    S3_folder: Optional[str] = None
    file_name: Optional[List[str]] = None
    mode: Optional[str] = "single"
    Local_folder: Optional[str] = None

# Ingestion Request
class IngestionRequestModel(BaseModel):
    type: Literal["FILE_INSERT", "QA_FILE_INSERT", "QA_INPUT_INSERT"]
    input_data: InputData

    @model_validator(mode="after")
    def validate_fields(self) -> 'IngestionRequestModel':
        if self.type == "QA_INPUT_INSERT":
            if not self.input_data.data:
                raise ValueError("'data' is required for QA_INPUT_INSERT and must be non-empty")
        elif self.type == "FILE_INSERT":
            if not self.input_data.metafield.doc_id:
                raise ValueError("'doc_id' is required for FILE_INSERT")
        return self

# DeleteQA request models
class DeleteQAItem(BaseModel):
    id: str

class DeleteQAInputData(BaseModel):
    metafield: MetaField
    data: List[DeleteQAItem]

class DeleteQARequestModel(BaseModel):
    input_data: DeleteQAInputData


class UpdateQAItem(BaseModel):
    id: str
    question: str = Field(..., description="The question to be updated")

class UpdateQAInputData(BaseModel):
    metafield: MetaField
    data: List[UpdateQAItem]

class UpdateQARequestModel(BaseModel):
    input_data: UpdateQAInputData

    @model_validator(mode="after")
    def validate_fields(self) -> 'UpdateQARequestModel':
        if not self.input_data.data:
            raise ValueError("'data' is required and must be non-empty")
        return self
