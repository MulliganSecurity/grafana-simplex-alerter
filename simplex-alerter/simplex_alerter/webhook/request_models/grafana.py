from pydantic import BaseModel


class GrafanaAlert(BaseModel):
    title: str
    message: str

    def render(self):
        return f"{self.title}\n{self.message}"
