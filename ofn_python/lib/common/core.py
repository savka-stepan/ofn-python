import requests


class OFNData:
    def __init__(self, server_name, headers, params):
        self.server_name = server_name
        self.headers = headers
        self.params = params
        self.order_data = {}
        self.product_data = {}

    def get_order_data(self, order_no):
        """Get order details."""
        url = f"{self.server_name}/api/orders/{order_no}"
        response = requests.get(url, headers=self.headers, params=self.params)
        self.order_data = response.json()

    def get_product_data(self, product_name):
        """Get product details."""
        url = f"{self.server_name}/api/products/bulk_products?q[name_eq]={product_name}"
        response = requests.get(url, headers=self.headers, params=self.params)
        self.product_data = response.json()

    def get_product_data_cont(self, product_name):
        """Get product details."""
        url = (
            f"{self.server_name}/api/products/bulk_products?q[name_cont]={product_name}"
        )
        response = requests.get(url, headers=self.headers, params=self.params)
        self.product_data = response.json()

    def get_variants_by_sku(self, sku):
        """Get variants details."""
        url = f"{self.server_name}/api/products/bulk_products/variants?q[sku_eq]={sku}"
        response = requests.get(url, headers=self.headers, params=self.params)
        return response.json()

    def get_product_data_by_variant_id(self, variant_id):
        """Get product details by variant id."""
        url = f"{self.server_name}/api/products/bulk_products?q[variants_id_eq]={variant_id}"
        response = requests.get(url, headers=self.headers, params=self.params)
        self.product_data = response.json()
