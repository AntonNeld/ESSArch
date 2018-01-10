from elasticsearch_dsl import analyzer, tokenizer, DocType, MetaField, Date, Integer, Keyword, Object, Text, Nested

ngram_tokenizer=tokenizer('custom_ngram_tokenizer', type='ngram', min_gram=1,
                          max_gram=15, token_chars=['letter', 'digit',
                                                    'punctuation', 'symbol'])
ngram_analyzer = analyzer('custom_ngram_analyzer', tokenizer=ngram_tokenizer,
                          filter=['lowercase'])


class Tag(DocType):
    name = Text(analyzer=ngram_analyzer, search_analyzer='standard')
    desc = Text()
    parents = Object()
    reference_code = Keyword()
    start_date = Date()
    end_date = Date()

    class Meta:
        index = 'tags'


class Archive(Tag):
    class Meta:
        index = 'tags'


class Series(Tag):
    class Meta:
        index = 'tags'


class Volume(Tag):
    class Meta:
        index = 'tags'

class Activity(Tag):
    class Meta:
        index = 'tags'

class ProcessGroup(Tag):
    class Meta:
        index = 'tags'

class Process(Tag):
    class Meta:
        index = 'tags'

class Document(Tag):
    terms_and_condition = Keyword()
    class Meta:
        index = 'tags'


class Component(DocType):
    unit_ids = Nested()  # unitid
    unit_dates = Nested()  # unitdate
    title = Text(analyzer=ngram_analyzer, search_analyzer='standard')  # unittitle
    desc = Text(analyzer=ngram_analyzer, search_analyzer='standard')  # e.g. from <odd>
    type = Keyword()  # series, volume, etc.
    parent = Keyword()
    related = Keyword()  # list of ids for components describing same element in other archive/structure
    archive = Keyword()

    class Meta:
        index = 'archive'
        doc_type = 'component'


class Archive(DocType):
    unit_ids = Nested()  # unitid
    unit_dates = Nested()  # unitdate
    title = Text(analyzer=ngram_analyzer, search_analyzer='standard')  # unittitle
    desc = Text(analyzer=ngram_analyzer, search_analyzer='standard')  # e.g. from <odd>
    type = Keyword()
    institution = Keyword()

    class Meta:
        index = 'archive'
        doc_type = 'archive'
