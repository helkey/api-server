import argparse
import cgi
import logging

# Python 3 libraries
import http.server as BaseHTTPServer
import json
import socketserver
import urllib.parse as urlparse

import garage as grg
parking = grg.Parking()


class HTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """
    Very simple view and request handler for "parking garage"
    In a production system, we would use more elaborate frameworks such as Flask.
    """

    def do_POST(self):
        """Serve a POST request: See Challenge description for details"""
        # logger = logging.getLogger('do_POST')
        logger.debug('Handling POST request: %s', self.path)

        if self.path == '/park':
            params = self._parse_POST_data()
            # return_code = 200
            # return_data = {'error': 'TODO'}
            return_code, return_data = validate_park(params)
        elif self.path == '/unpark':
            params = self._parse_POST_data()
            return_code = 200
            # return_data = {'error': 'TODO'}
            return_code, return_data = validate_unpark(params)
        else:
            return_code = 404
            return_data = {'error': 'Unsupported Command'}

        return_data_formatted = json.dumps(return_data, indent=' ')

        self.log_request(code=return_code)
        self.send_response(code=return_code)
        self.send_header('Content-Length', len(return_data_formatted))
        self.end_headers()
        # socketserve library expects UTF-8 encoding
        return_data = return_data_formatted.encode(encoding='utf-8', errors='strict')
        self.wfile.write(return_data)

    def _parse_POST_data(self):
        """
                Read HTTP POST data from the request and return request parameters as dictionary
        
                :return: Request parameters
                :rtype: dict[str,str]
        """
        try:
            ctype, pdict = cgi.parse_header(self.headers['content-type'])
        except KeyError:
            postvars = {}
        else:
            if ctype == 'multipart/form-data':
                postvars = cgi.parse_multipart(self.rfile, pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                length = int(self.headers['content-length'])
                postvars = urlparse.parse_qs(self.rfile.read(length), keep_blank_values=1)
            else:
                postvars = {}
                # for simplicity, we take the first value specified in the request, if a parameter occurs
                # more than once
        return {key: value[0] for key, value in postvars.items() if value}


# NOTE: Use validator class if API more complex (e.g. http://docs.python-cerberus.org, etc)
param_err = 400 # parameter errors
lot_full = 406  # unable to assign parking space
sys_error = 500 # system error
def validate_park(params):
    try:
        size = params[b'size']
    except:
        return param_err, {'error': 'Need to supply car size'}
    large_car = (size == b'large_car')
    if not size and size != b'small_car':
        return param_err, {'error': 'Invalid car size'}
    
    try:
        handicap = params[b'has_handicapped_placard']
    except:
        return param_err, {'error': 'Need to supply *has_handicapped_placard* arg'}
    handicapped = (handicap == b'1')
    if not handicapped and handicap != b'0':
        return param_err, {'error': 'Invalid *has_handicapped_placard* value'}

    try:
        i_set, i_slot = parking.assign_space(handicapped, large_car) 
        level, row, space = grg.toLevel_Row_Space(i_set, i_slot)
        # Convert from zero-based (program) to one-based (UI)
        return 200, {"level": level + 1, "row": row + 1, "space": space + 1}
    except:
        return lot_full, {'error': 'Unable to allocate space'}
       
err_empty = 412 # unparked car from empty space
def validate_unpark(params):
    try:
        level = params[b'level']
        row = params[b'row']
        space = params[b'space']
    except:
        # Needs more detailed validation errors
        return param_err, {'error': 'Invalid -unpark- parameters'}
    try:
        # Use table loop of level/row/space to validate values
        lvl, rw, spc = int(level), int(row), int(space)
        # Convert from one-based (UI) to zero-based (program)
        i_set, i_slot = grg.toSet_Slot(lvl - 1, rw - 1, spc - 1)
    except:
        return param_err, {'error': 'Invalid -unpark- values'}
    try:
        t_parked, car_type = parking.release_space(i_set, i_slot)
        amount = grg.parking_amount(car_type, i_set, t_parked, grg.time_rec())
        return 200, {'amount': amount}
    except:
        return err_empty, {'error': 'No car in this space'}


if __name__ == '__main__':
    print("Parking Garage...")
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--host', default='', type=str, help='IP to bind on (default: all)')
    parser.add_argument(
        '--port', default=8080, type=int, help='HTTP port to listen on (default: %(default)s)'
    )
    args = parser.parse_args()
    # NOTE: For simplicity, we assume the rest of the input is sensible
    if args.port <= 0 or args.port > 65536:
        args.error('Invalid --port')
        
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format='%(asctime)s %(message)s',
        datefmt='%Y-%m-%d %I:%M:%S %p'
    )
    logger = logging.getLogger()
    
    bind_on = (args.host, args.port)
    logger.info('Starting server on %s', bind_on)
    httpd = socketserver.TCPServer(bind_on, HTTPRequestHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info('Received shutdown request')
    finally:
        logger.info('Shutting down')
        httpd.server_close()

# curl --verbose --data 'size=compact_car' --data 'has_handicapped_placard=1' 127.0.0.1:8080/park
# curl --verbose --data 'level=1' --data 'row=1' --data 'space=1' 127.0.0.1:8080/unpark
