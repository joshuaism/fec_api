from django.shortcuts import render
from django.http import StreamingHttpResponse
import requests
import json
import os

api_key = os.environ.get('FEC_API_KEY')

# Create your views here.
def scheduleA(request):
    names = request.GET.getlist('name')
    employers = request.GET.getlist('employer')
    committees = request.GET.getlist('committee')
    cycles = request.GET.getlist('cycle')
    occupations = request.GET.getlist('occupation')
    committee_types = request.GET.getlist('committee_type')
    cities = request.GET.getlist('city')
    state = request.GET.get('state')
    url = create_url(names, employers, committees, cycles, occupations, committee_types, cities, state)
    stream = iterator(url)
    response = StreamingHttpResponse(stream, status=200, content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response

def react(request):
    names = request.GET.getlist('name')
    employers = request.GET.getlist('employer')
    committees = request.GET.getlist('committee')
    cycles = request.GET.getlist('cycle')
    occupations = request.GET.getlist('occupation')
    committee_types = request.GET.getlist('committee_type')
    cities = request.GET.getlist('city')
    state = request.GET.get('state')
    url = create_url(names, employers, committees, cycles, occupations, committee_types, cities, state)
    stream = react_iterator(url)
    response = StreamingHttpResponse(stream, status=200, content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response

def transform(item):
    item['fullName'] = item['contributor_name']
    item['occupation'] = item['contributor_occupation']
    item['employer'] = item['contributor_employer']
    item['address'] = item['contributor_street_1']
    item['city'] = item['contributor_city']
    item['state'] = item['contributor_state']
    item['amount'] = item['contribution_receipt_amount']
    item['date'] = item['contribution_receipt_date']
    if item['memo_text']:
        item['earmark'] = item['memo_text']
    elif item['receipt_type_full']:
        item['earmark'] = item['receipt_type_full']
    if item['committee'] is not None:
        item['committee']['id'] = item['committee']['committee_id']
        item['committee']['type'] = item['committee']['committee_type']
        item['committee']['party'] = item['committee']['party_full']
        if item['committee']['party'] is None:
            item['committee']['party'] = 'unknown'
    return item

def iterator(url):
    print(f'requesting: {url}')
    request=requests.get(url)

    response_dict = request.json()
    results = response_dict
    for item in results['results']:
        item = transform(item)
    pagination = response_dict['pagination']
    pages = pagination['pages']
    if pagination['last_indexes']:
        last_index = pagination['last_indexes']['last_index']
        last_amount = pagination['last_indexes']['last_contribution_receipt_amount']
    if pages > 20:
        pages = 20

    print(f'return 1 of {pages}')
    yield f"data: {json.dumps(results)}\n\n"

    for i in range(2, pages + 1):
        page_query = f"&last_index={last_index}&last_contribution_receipt_amount={last_amount}"
        request=requests.get(url + page_query)
        response_dict = request.json()
        #results.extend(response_dict['results'])
        results = response_dict
        for item in results['results']:
            item = transform(item)
        pagination = response_dict['pagination']
        last_index = pagination['last_indexes']['last_index']
        last_amount = pagination['last_indexes']['last_contribution_receipt_amount']
        print(f'return {i} of {pages}')
        yield f"data: {json.dumps(results)}\n\n"

def react_iterator(url):
    print(f'requesting: {url}')
    request=requests.get(url)

    response_dict = request.json()
    results = response_dict
    for item in results['results']:
        item = transform(item)
    pagination = response_dict['pagination']
    pages = pagination['pages']
    if pagination['last_indexes']:
        last_index = pagination['last_indexes']['last_index']
        last_amount = pagination['last_indexes']['last_contribution_receipt_amount']
    if pages > 10:
        pages = 10

    print(f'return 1 of {pages}')
    yield f"[{json.dumps(results)}"

    for i in range(2, pages + 1):
        page_query = f"&last_index={last_index}&last_contribution_receipt_amount={last_amount}"
        request=requests.get(url + page_query)
        response_dict = request.json()
        #results.extend(response_dict['results'])
        results = response_dict
        for item in results['results']:
            item = transform(item)
        pagination = response_dict['pagination']
        last_index = pagination['last_indexes']['last_index']
        last_amount = pagination['last_indexes']['last_contribution_receipt_amount']
        print(f'return {i} of {pages}')
        yield f", {json.dumps(results)}"
    yield "]"

def create_url(names, employers, committees, cycles, occupations, committee_types, cities, state):
    url='https://api.open.fec.gov/v1/schedules/schedule_a/'
    query_string = '?api_key=' + api_key
    query_string = query_string + '&sort=-contribution_receipt_amount&per_page=100'
    query_string = query_string + add_parameter('&contributor_name=', names)
    query_string = query_string + add_parameter('&contributor_employer=', employers)
    query_string = query_string + add_parameter('&committee_id=',committees)
    query_string = query_string + add_parameter('&two_year_transaction_period=',cycles)
    query_string = query_string + add_parameter("&contributor_occupation=", occupations)
    query_string = query_string + add_parameter("&recipient_committee_type=", committee_types)
    query_string = query_string + add_parameter("&contributor_city=", cities)
    if (state):
        query_string = query_string + "&contributor_state=" + state

    return url + query_string

def add_parameter(param, vals):
    query = ""
    for v in vals:
        query = query + param + v
    return query


