"""
to import the modules correctly 
pip install "pyramid==1.8.3" 
"""
from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.request import Request
import json
import DataReaderplus as dr

def university_retrieval(request):
	dataReader = dr.DataReader()
	userID = request.matchdict['id']
	tech_ids = dataReader.get_university_tech_ids(userID)
	university_tech_dict = {"university": userID, "technology": tech_ids}
	response = Response(json.dumps(university_tech_dict))
	response.headerlist.extend(
		(
			('Access-Control-Allow-Origin', '*'),
			('Access-Control-Allow-Headers', 'Access-Control-Allow-Origin'),
			('Access-Control-Allow-Method', 'GET'),
			('Content-Type', 'application/json')
		)
	)
	return response

if __name__ == '__main__':
    config = Configurator()
    config.add_route('university', '/university/{id}')
    config.add_view(university_retrieval, route_name='university')
    app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 8080, app)
    server.serve_forever()