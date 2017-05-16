import json
import re
import requests
from requests.adapters import HTTPAdapter
import time
import traceback

try:
    from urllib import urlencode
except:
    from urllib.parse import urlencode

class Hypothesis:
    def __init__(self, 
                 domain=None, 
                 authority=None, 
                 username=None, 
                 token=None, 
                 group=None, 
                 limit=None, 
                 max_search_results=None, 
                 host=None, 
                 port=None,
                 debug=False):

        if domain is None:
            self.domain = 'hypothes.is'
        else:
            self.domain = domain

        if authority is None:
            self.authority = 'hypothes.is'
        else:
            self.authority = authority

        self.app_url = 'https://%s/app' % self.domain
        self.api_url = 'https://%s/api' % self.domain
        self.query_url = 'https://%s/api/search?{query}' % self.domain
        self.anno_url = 'https://%s/a' % domain
        self.via_url = 'https://via.hypothes.is'
        self.token = token
        self.username = username
        self.single_page_limit = 200 if limit is None else limit  # per-page, the api honors limit= up to (currently) 200
        self.max_search_results = 2000 if max_search_results is None else max_search_results  # limit for paginated results
        self.group = group if group is not None else '__world__'
        if self.username is not None:
            self.permissions = {
                "read": ['group:' + self.group],
                "update": ['acct:' + self.username + '@' + self.authority],
                "delete": ['acct:' + self.username + '@' + self.authority],
                "admin":  ['acct:' + self.username + '@' + self.authority]
                }
        else: self.permissions = {}

        self.session = requests.Session()
        self.session.mount(self.api_url, HTTPAdapter(max_retries=3))

        self.debug = True

    def search_all(self, params={}):
        """Call search API with pagination, return row iterator """
        if not 'offset' in params:
            params['offset'] = 0
        params['limit'] = self.single_page_limit
        while True:
            h_url = self.query_url.format(query=urlencode(params, True))
            if self.debug:
                print ( h_url )
            if self.token is not None:
                r = self.token_authenticated_get(h_url)
                obj = r
            else:
                r = self.session.get(h_url)
                obj = r.json()
            rows = obj['rows']
            row_count = len(rows)
            if self.debug:
                print ( "%s rows" % row_count )
            if 'replies' in obj:
               rows += obj['replies']
            row_count = len(rows)
            print ( "%s rows+replies" % row_count )
            params['offset'] += row_count
            if params['offset'] > self.max_search_results:
                break
            if len(rows) is 0:
                break
            for row in rows:
                yield row

    def token_authenticated_get(self, url=None):
        try:
           headers = {'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json;charset=utf-8' }
           r = requests.get(url, headers=headers)
           return r.json()
        except:
            print ( traceback.print_exc() )

    def get_annotation(self, id=None):
        h_url = '%s/annotations/%s' % ( self.api_url, id )
        if self.token is not None:
            obj = self.token_authenticated_get(h_url)
        else:
            obj = requests.get(h_url)
        return obj

    def post_annotation(self, payload):
        try:
            headers = {'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json;charset=utf-8' }
            data = json.dumps(payload, ensure_ascii=False)
            r = requests.post(self.api_url + '/annotations', headers=headers, data=data.encode('utf-8'))
            return r
        except:
            e = traceback.print_exc()
            return None

    def update_annotation(self, id, payload):
        headers = {'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json;charset=utf-8' }
        data = json.dumps(payload, ensure_ascii=False)
        r = requests.put(self.api_url + '/annotations/' + id, headers=headers, data=data)
        return r
    
    def delete_annotation(self, id):
       headers = {'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json;charset=utf-8' }
       r = requests.delete(self.api_url + '/annotations/' + id, headers=headers)
       return r 

class HypothesisAnnotation:
    """Encapsulate one row of a Hypothesis API search."""   
    def __init__(self, row):
        self.type = None
        self.id = row['id']
        self.group = row['group']
        self.updated = row['updated'][0:19]
        self.permissions = row['permissions']
        self.user = row['user'].replace('acct:','').replace(self.authority,'')
        self.is_group = self.group not in [None, '__world__', 'NoGroup']
        self.is_world_private = not self.is_group and 'group:__world__' not in self.permissions['read']
        self.is_group_private = self.is_group and 'group:'+self.group not in self.permissions['read']
        self.is_public = not self.is_group and not self.is_group_private and not self.is_world_private

        if 'uri' in row:    # is it ever not?
            self.uri = row['uri']
        else:
             self.uri = "no uri field for %s" % self.id
        self.uri = self.uri.replace('https://via.hypothes.is/h/','').replace('https://via.hypothes.is/','')

        if self.uri.startswith('urn:x-pdf') and 'document' in row:
            if 'link' in row['document']:
                self.links = row['document']['link']
                for link in self.links:
                    self.uri = link['href']
                    if self.uri.startswith('urn:') == False:
                        break
            if self.uri.startswith('urn:') and 'filename' in row['document']:
                self.uri = row['document']['filename']

        if 'document' in row and 'title' in row['document']:
            t = row['document']['title']
            if isinstance(t, list) and len(t):
                self.doc_title = t[0]
            else:
                self.doc_title = t
        else:
            self.doc_title = None
        if self.doc_title is None:
            self.doc_title = ''
        self.doc_title = self.doc_title.replace('"',"'")
        if self.doc_title == '': self.doc_title = 'untitled'

        self.tags = []
        if 'tags' in row and row['tags'] is not None:
            self.tags = row['tags']
            if isinstance(self.tags, list):
                self.tags = [t.strip() for t in self.tags]

        self.text = ''
        if 'text' in row:
            self.text = row['text']

        self.references = []
        if 'references' in row:
            self.type = 'reply'
            self.references = row['references']

        self.target = []
        if 'target' in row:
            self.target = row['target']

        self.is_page_note = False
        try:
            if self.references == [] and self.target is not None and len(self.target) and isinstance(self.target, list) and not 'selector' in self.target[0]:
                self.is_page_note = True
                self.type = 'pagenote'
        except:
            traceback.print_exc()
        if 'document' in row and 'link' in row['document']:
            self.links = row['document']['link']
            if not isinstance(self.links, list):
                self.links = [{'href':self.links}]
        else:
            self.links = []

        self.start = self.end = self.prefix = self.exact = self.suffix = None
        try:
            if isinstance(self.target,list) and len(self.target) and 'selector' in self.target[0]:
                self.type = 'annotation'
                selectors = self.target[0]['selector']
                for selector in selectors:
                    if 'type' in selector and selector['type'] == 'TextQuoteSelector':
                        try:
                            self.prefix = selector['prefix']
                            self.exact = selector['exact']
                            self.suffix = selector['suffix']
                        except:
                            traceback.print_exc()
                    if 'type' in selector and selector['type'] == 'TextPositionSelector' and 'start' in selector:
                        self.start = selector['start']
                        self.end = selector['end']
                    if 'type' in selector and selector['type'] == 'FragmentSelector' and 'value' in selector:
                        self.fragment_selector = selector['value']
        except:
            print ( traceback.format_exc() )
