

class RawItem(object):
    def __init__(self, raw_content, page_num, city_id):
        self.raw_content = raw_content
        self.page_num = page_num
        self.city_id = city_id


    def extract_info(self):
        self.id = self.city_id + 'dummy'
        self.corp_name = 'dummy'
        self.introduction = 'dummy'
        self.product = 'dummy'
        self.website = 'dummy'
        self.website_title = 'dummy'


    def get_info_as_tuple(self):
        return (
            self.id,
            self.corp_name,
            self.introduction,
            self.product,
            self.website,
            self.website_title
        )



