##############################################################################
#                                                                            #
#   Microservices header template                                            #
#   License: MIT                                                             #
#   Copyright (c) 2017 Crown Copyright (Office for National Statistics)      #
#                                                                            #
##############################################################################
from ons_ras_common import ons_env

if __name__ == '__main__':
    ons_env.activate()



#from connexion import App
#from flask_cors import CORS
#from .encoder import JSONEncoder
#from .configuration import ons_env

#if __name__ == '__main__':
#    ons_env.activate()
#    app = App(__name__, specification_dir='./swagger/')
#    CORS(app.app)
#    app.app.json_encoder = JSONEncoder
#    app.add_api('swagger.yaml', arguments={'title': 'ONS Microservice'})
#    app.run(host='0.0.0.0', port=ons_env.port)

    #from twisted.internet import reactor
    #from flask_twisted import Twisted
    #reactor.callLater(1, print, '<<Twisted is running>>')
    #Twisted(app).run(port=getenv('PORT',8080))