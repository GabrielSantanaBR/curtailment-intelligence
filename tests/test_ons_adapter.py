import pytest

from ml.ons_adapter import detect_mapping, normalize_name, read_csv_flexible


def test_normalize_portuguese_name():
    assert normalize_name("Geração Verificada (MW)") == "geracao_verificada_mw"


def test_detect_mapping():
    mapping = detect_mapping(["din_instante", "id_ons", "nom_usina", "nom_subsistema"])
    assert mapping["timestamp"] == "din_instante"
    assert mapping["plant_code"] == "id_ons"


def test_read_csv_flexible_accepts_semicolon(tmp_path):
    path = tmp_path / "sample.csv"
    path.write_text("din_instante;id_ons\n2026-01-01T00:00:00Z;X\n", encoding="utf-8")

    with path.open("rb") as handle:
        dataframe = read_csv_flexible(handle)

    assert list(dataframe.columns) == ["din_instante", "id_ons"]


def test_read_csv_flexible_rejects_single_column(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("only_one_column\nvalue\n", encoding="utf-8")

    with path.open("rb") as handle, pytest.raises(ValueError):
        read_csv_flexible(handle)
