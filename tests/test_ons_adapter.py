import pandas as pd
from ml.ons_adapter import normalize_name,detect_mapping

def test_normalize_portuguese_name(): assert normalize_name("Geração Verificada (MW)")=="geracao_verificada_mw"
def test_detect_mapping():
    m=detect_mapping(["din_instante","id_ons","nom_usina","nom_subsistema"])
    assert m["timestamp"]=="din_instante" and m["plant_code"]=="id_ons"
