import hypothesis, os, time, unittest

class Test(unittest.TestCase):
    def setUp(self):
        self.h = hypothesis.Hypothesis(
            domain="hypothes.is",
            authority="hypothes.is",
            username=os.environ["HYPOTHESIS_USERNAME"],
            token=os.environ["HYPOTHESIS_TOKEN"],
            debug=False,
        )

        self.test_uri = "http://www.example.com"
        self.world_group = "__world__"
        self.test_group = "47bayzz9"  # HYPOTHESIS_USERNAME must belong to this group
        self.prefix = "ts. You may use this\n    domain "
        self.suffix = " without prior coordination or a"
        self.exact = "in examples"
        self.text = "Hypothesis API wrapper test 3219099"
        self.tags = ["HypothesisTest", "3219099"]

        self.payload = {
            "uri": self.test_uri,
            "target": [
                {
                    "source": [self.test_uri],
                    "selector": [
                        {
                            "type": "TextQuoteSelector",
                            "prefix": self.prefix,
                            "exact": self.exact,
                            "suffix": self.suffix,
                        }
                    ],
                }
            ],
            "text": self.text,
            "tags": self.tags,
            "permissions": self.h.permissions,
            "group": self.world_group,
        }

        self.current_id = None

    def test_01_search_500(self):
        results = self.h.search_all({"max_results": 500})
        i = 0
        for result in results:
            i += 1
            pass
        assert i == 500

    def test_02_post_and_delete_public_annotation(self):
        r = self.h.post_annotation(self.payload)
        obj = r.json()
        assert r.status_code == 200
        assert len(obj["tags"]) == 2
        assert obj["uri"] == self.test_uri
        assert obj["group"] == self.world_group
        id = obj["id"]
        time.sleep(1)
        r = self.h.get_annotation(id)
        assert r["id"] == id
        r = self.h.delete_annotation(id)
        assert r.status_code == 200
        time.sleep(1)
        with self.assertRaises(Exception):
            self.h.get_annotation(id)

    def test_03_post_and_delete_group_annotation(self):
        payload = self.payload
        payload["group"] = self.test_group
        r = self.h.post_annotation(payload)
        obj = r.json()
        assert r.status_code == 200
        assert len(obj["tags"]) == 2
        assert obj["uri"] == self.test_uri
        assert obj["group"] == self.test_group
        id = obj["id"]
        time.sleep(1)
        r = self.h.get_annotation(id)
        assert r["id"] == id
        r = self.h.delete_annotation(id)
        assert r.status_code == 200
        time.sleep(1)
        with self.assertRaises(Exception):
            self.h.get_annotation(id)

    def test_04_parse_and_delete_public_annotation(self):
        payload = self.payload
        r = self.h.post_annotation(payload)
        obj = r.json()
        assert r.status_code == 200
        assert len(obj["tags"]) == 2
        assert obj["uri"] == self.test_uri
        assert obj["group"] == self.world_group
        time.sleep(1)
        id = obj["id"]
        r = self.h.get_annotation(id)
        assert r["id"] == id
        anno = hypothesis.HypothesisAnnotation(r)
        assert anno.id == id
        assert anno.uri == self.test_uri
        assert anno.is_page_note is False
        assert anno.is_public is True
        assert anno.references == []
        assert anno.group == self.world_group
        assert anno.tags == self.tags
        assert anno.user == os.environ["HYPOTHESIS_USERNAME"] + "@hypothes.is"
        assert anno.target[0]["selector"][0]["exact"] == self.exact
        r = self.h.delete_annotation(id)
        assert r.status_code == 200
        time.sleep(1)
        with self.assertRaises(Exception):
            self.h.get_annotation(id)

    def test_05_post_and_delete_public_pagenote(self):
        payload = self.payload
        del payload["target"]
        r = self.h.post_annotation(self.payload)
        obj = r.json()
        assert r.status_code == 200
        assert len(obj["tags"]) == 2
        assert obj["uri"] == self.test_uri
        assert obj["group"] == self.world_group
        id = obj["id"]
        time.sleep(1)
        r = self.h.get_annotation(id)
        assert r["id"] == id
        anno = hypothesis.HypothesisAnnotation(r)
        assert anno.is_page_note
        r = self.h.delete_annotation(id)
        assert r.status_code == 200
        time.sleep(1)
        with self.assertRaises(Exception):
            self.h.get_annotation(id)

    def test_06_update_and_delete_group_annotation(self):
        payload = self.payload
        payload["group"] = self.test_group
        r = self.h.post_annotation(payload)
        obj = r.json()
        assert r.status_code == 200
        assert len(obj["tags"]) == 2
        assert obj["uri"] == self.test_uri
        assert obj["group"] == self.test_group
        id = obj["id"]
        time.sleep(1)
        r = self.h.get_annotation(id)
        assert r["id"] == id
        payload = {
          "text":"updated text",
        }
        r = self.h.update_annotation(id, payload)
        time.sleep(1)
        assert r.status_code == 200
        time.sleep(1)
        r = self.h.get_annotation(id)
        assert r["text"] == "updated text"
        time.sleep(1)
        r = self.h.delete_annotation(id)
        assert r.status_code == 200
        time.sleep(1)
        with self.assertRaises(Exception):
            self.h.get_annotation(id)
if __name__ == "__main__":
    unittest.main()
