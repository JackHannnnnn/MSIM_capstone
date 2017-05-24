from pyramid.view import view_config
from pyramid.request import Request
from pyramid.response import Response
import json
import DataReaderViz as dr
import matchUsers

@view_config(route_name='home', renderer='templates/homepage.jinja2')
def home_view(request):
    return {'project': 'visualization'}

@view_config(route_name='university',
             renderer='templates/university.jinja2')
def university_view(request):
    return {'university': request.matchdict['id']}

@view_config(route_name='university_data', renderer='json')
def university_data_view(request):
    dataReader = dr.DataReader()
    universityID = request.matchdict['id']
    # retrieve technology ids published by the university
    tech_ids = dataReader.get_techID_by_university(universityID)

    if universityID=="all": # retrieve data for all university page
        
        tech_views = dataReader.get_user_views(tech_ids) # count of views on each technology
        tech_emails = dataReader.email_sent_per_tech() # count of email sent on each technology
        contacted_keywords = dataReader.all_contacted_keywords() # keywords frequency of all contacted technologies
        response = Response(json.dumps({"tech_views": tech_views, "tech_emails": tech_emails, "keywords": contacted_keywords}))
    else:
        
        tech_views = dataReader.get_user_views(tech_ids) # count of views on each technology
        user_keywords = dataReader.get_user_keywords_of_viewed_tech(tech_ids, universityID) # top keywords of users viewing the technology
        tech_keywords = dataReader.get_tech_keywords(tech_ids) # all keywords across all technologies
        viewed_users = dataReader.get_tech_viewed_user(tech_ids) # company ids which viewed the technology
        emails = dataReader.email_sent_vs_click(tech_ids) # email sent vs clicks per technology
        matched_users = matchUsers.find_match(tech_ids) # sthe most relevant users for each technology
        response = Response(json.dumps({"tech_views": tech_views, "user_keywords": user_keywords, "tech_keywords": tech_keywords, "viewed_users": viewed_users, "emails": emails, "matches": matched_users}))

    response.headerlist.extend(
		(
			('Access-Control-Allow-Origin', '*'),
			('Access-Control-Allow-Headers', 'Access-Control-Allow-Origin'),
			('Access-Control-Allow-Method', 'GET'),
			('Content-Type', 'application/json')
		)
	)
    return response

def all_university_view(request):
    return {'project': 'visualization'}