import lighttools.instinfo as instinfo
import lighttools.config as config


def test_list_products():
    products = instinfo.list_products(prefix="LightTools")
    assert config.VERSION in products


def test_query():
    install_data = instinfo.query(product=config.VERSION)
    assert install_data["DisplayName"] == config.VERSION
