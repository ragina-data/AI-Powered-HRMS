
from pydantic import BaseModel, ConfigDict, Field, field_validator


class HRPolicyCreate(BaseModel):
    policy_code: str = Field(
        min_length=1,
        max_length=50,
    )

    policy_title: str = Field(
        min_length=1,
        max_length=250,
    )

    category: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
    )

    version_label: str | None = Field(
        default=None,
        max_length=50,
    )

    change_summary: str | None = Field(
        default=None,
    )

    @field_validator(
        "policy_code",
        "policy_title",
        "category",
    )
    @classmethod
    def validate_non_blank(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("This field cannot be blank.")

        return value

class HRPolicyCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    policy_id: int
    policy_code: str
    policy_title: str
    category: str
    status: str
    policy_version_id: int
    version_number: int
    version_label: str | None
    version_status: str
class HRPolicyIngestionResponse(BaseModel):
    policy_version_id: int
    source_file_name: str
    chunks_created: int
    status: str