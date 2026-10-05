from scanpro.services.naps2 import discover_devices

def test_discover_parser(monkeypatch):
    sample = (
        "Brother ADS-2600We (airscan:ip=192.168.0.172)\n"
        "Samsung C48x Series (SEC30CDA7AE3870) (airscan:ip=192.168.0.3)\n"
    )

    monkeypatch.setattr("scanpro.services.naps2.list_devices", lambda driver="sane": sample)
    devices = discover_devices("sane")

    assert len(devices) == 2
    assert devices[0]["name"] == "Brother ADS-2600We"
    assert devices[0]["address"] == "192.168.0.172"
    assert devices[0]["driver"] == "sane"
    assert devices[1]["name"] == "Samsung C48x Series (SEC30CDA7AE3870)"
    assert devices[1]["address"] == "192.168.0.3"
