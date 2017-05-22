from pyramid.view import view_config
from pyramid.request import Request
from pyramid.response import Response
import json
import DataReaderplus as dr
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
    # retrieve count of views on each technology
    tech_views = dataReader.get_user_views(tech_ids)
    # retrieve top keywords of users viewing the technology
    user_keywords = dataReader.get_user_keywords_of_viewed_tech(tech_ids)
    # retrieve all keywords across all technologies
    tech_keywords = dataReader.get_tech_keywords(tech_ids)
    # retrieve company ids which viewed the technology
    viewed_users = dataReader.get_tech_viewed_user(tech_ids)
    # retrieve email sent vs clicks per technology
    emails = dataReader.email_sent_vs_click(tech_ids)
    matched_users = matchUsers.find_match(tech_ids)

    response = Response(json.dumps({"tech_views": tech_views,
                                    "user_keywords": user_keywords,
                                    "tech_keywords": tech_keywords,
                                    "viewed_users": viewed_users,
                                    "emails": emails,
                                    "matches": matched_users}))
    response.headerlist.extend(
		(
			('Access-Control-Allow-Origin', '*'),
			('Access-Control-Allow-Headers', 'Access-Control-Allow-Origin'),
			('Access-Control-Allow-Method', 'GET'),
			('Content-Type', 'application/json')
		)
	)
    return response

@view_config(route_name = 'all_university_data', renderer = 'json')
def all_university_data_view(request):
    dataReader = dr.DataReader()
    # retrieve tech views data for all universities
    tech_views_all = dataReader.get_user_views_all()
    # retrieve email sent data for each tech for all universities
    emails_sent_all = dataReader.email_sent_all_tech()
    response = Response(json.dumps({"tech_views_all": tech_views_all,
                                    "emails_sent_all": emails_sent_all}))
    response.headerlist.extend(
        (
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Headers', 'Access-Control-Allow-Origin'),
            ('Access-Control-Allow-Method', 'GET'),
            ('Content-Type', 'application/json')
        )
    )
    return response

@view_config(route_name='all_university',
             renderer='templates/all_university.jinja2')
def all_university_view(request):
    return {'project': 'visualization'}