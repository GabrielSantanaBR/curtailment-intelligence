from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./curtailment.db"
    model_dir: str = "artifacts"
    demo_data_path: str = "data/demo/curtailment_demo.csv"
    frontend_origin: str = "http://localhost:5173"
    default_energy_value_brl_mwh: float = 220.0
    default_grid_factor_tco2_mwh: float = 0.08

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def resolve(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.project_root / path


settings = Settings()
