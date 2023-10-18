import json


class Product:
    def __init__(self, article_id, product_code, prod_name, product_type_no, product_type_name,
                 product_group_name, graphical_appearance_no, graphical_appearance_name,
                 colour_group_code, colour_group_name, perceived_colour_value_id,
                 perceived_colour_value_name, perceived_colour_master_id,
                 perceived_colour_master_name, department_no, department_name, index_code,
                 index_name, index_group_no, index_group_name, section_no, section_name,
                 garment_group_no, garment_group_name, detail_desc, image_path = "", embedding=[]):
        self.article_id = article_id
        self.product_code = product_code
        self.prod_name = prod_name
        self.product_type_no = product_type_no
        self.product_type_name = product_type_name
        self.product_group_name = product_group_name
        self.graphical_appearance_no = graphical_appearance_no
        self.graphical_appearance_name = graphical_appearance_name
        self.colour_group_code = colour_group_code
        self.colour_group_name = colour_group_name
        self.perceived_colour_value_id = perceived_colour_value_id
        self.perceived_colour_value_name = perceived_colour_value_name
        self.perceived_colour_master_id = perceived_colour_master_id
        self.perceived_colour_master_name = perceived_colour_master_name
        self.department_no = department_no
        self.department_name = department_name
        self.index_code = index_code
        self.index_name = index_name
        self.index_group_no = index_group_no
        self.index_group_name = index_group_name
        self.section_no = section_no
        self.section_name = section_name
        self.garment_group_no = garment_group_no
        self.garment_group_name = garment_group_name
        self.detail_desc = detail_desc
        self.image_path = image_path
        self.embedding = embedding

    def to_dict(self):
        # Convert the Product object to a dictionary
        product_dict = {
            "article_id": self.article_id,
            "product_code": self.product_code,
            "prod_name": self.prod_name,
            "product_type_no": self.product_type_no,
            "product_type_name": self.product_type_name,
            "product_group_name": self.product_group_name,
            "graphical_appearance_no": self.graphical_appearance_no,
            "graphical_appearance_name": self.graphical_appearance_name,
            "colour_group_code": self.colour_group_code,
            "colour_group_name": self.colour_group_name,
            "perceived_colour_value_id": self.perceived_colour_value_id,
            "perceived_colour_value_name": self.perceived_colour_value_name,
            "perceived_colour_master_id": self.perceived_colour_master_id,
            "perceived_colour_master_name": self.perceived_colour_master_name,
            "department_no": self.department_no,
            "department_name": self.department_name,
            "index_code": self.index_code,
            "index_name": self.index_name,
            "index_group_no": self.index_group_no,
            "index_group_name": self.index_group_name,
            "section_no": self.section_no,
            "section_name": self.section_name,
            "garment_group_no": self.garment_group_no,
            "garment_group_name": self.garment_group_name,
            "detail_desc": self.detail_desc,
            "image_path": self.image_path,
            "embedding": self.embedding
        }

        return product_dict
    
    def to_json(self):
        # Convert the Product object to a dictionary
        product_dict = self.to_dict()

        # Convert the dictionary to a JSON document
        json_doc = json.dumps(product_dict)
        return json_doc

