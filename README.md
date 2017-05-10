# Hypothesis
yet another python wrapper for the hypothes.is api

## Create an annotation using a TextQuoteSelector

```
h = hypothesis.Hypothesis(token='TOKEN')  # your api token from https://hypothes.is/account/developer

url = 'url of web page to annotate'
exact = 'selected text (i.e. the quote)'
prefix = '30 chars preceding the quote'
suffix = '30 chars following the quote'
title = 'title of the web page'
tags = ["tag1", "tag2"]
text = "body of annotation, can include [markup](http://example.com)"
   
payload = {
    "uri": url,
    "target": 
        [{
            "source": [url],
            "selector": 
                [{
                    "type": "TextQuoteSelector", 
                    "prefix": prefix,
                    "exact": exact,
                    "suffix": suffix
                    }
                 ]
        }], 
    "tags": tags,
    "text": text,
     "document": {
         "title": [title]
     }
}

r = h.create_annotation_with_custom_payload(payload)
print r.status_code
```
