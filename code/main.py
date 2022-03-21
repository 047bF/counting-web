from optparse import OptionParser
import requests
import string
import itertools
import redis
import datetime

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
redis = redis.Redis(
     host='localhost',
     port='6380')
protos = ['https://', 'http://']
headers = {'user-agent': 'python-requests/2.6.2 CPython/3.4.3 Windows/8'}


def generate_names(count):
    chars = string.ascii_lowercase + string.digits  # "abcdefghijklmnopqrstuvwxyz0123456789"
    for item in itertools.product(chars, repeat=count):
        yield "".join(item)


def get_status(proto, site_name, zone):
    web_url = proto + site_name + zone
    try:
        request = requests.get(web_url, headers=headers, stream=True, timeout=(10, 30))
        if request.status_code < 400:
            print('Web site exists: %s' % web_url)
            return request
    except:
        return None


def is_last_key(some_key):
    last_key = str(redis.hget('h_last_key', 'url'), 'cp1252')
    if last_key == some_key:
        return True
    else:
        return False


def set_last_key(url):
    time = datetime.datetime.now().strftime("%m/%d/%YT%H:%M:%S")
    redis.hset('h_last_key', 'time', time)
    redis.hset('h_last_key', 'url', url)


def insert_db(url, protocol, site_data):

    time = datetime.datetime.now().strftime("%m/%d/%YT%H:%M:%S")
    redis.hset(url, 'time', time)
    redis.hset(url, 'proto', protocol)
    try:
        data = '%s:%s - %i' % (site_data.raw.connection.sock.getpeername()[0],
                               site_data.raw.connection.sock.getpeername()[1],
                               site_data.status_code)
        redis.hset(url, 'data', data)
    except:
        redis.hset(url, 'data', 'Error')


def parse_arg():
    parser = OptionParser()
    parser.add_option("-n", "--name", dest="name", help="defined site name", metavar="NAME")
    parser.add_option("-c", "--count", dest="count", default=10, help="defined count of letters",
                      metavar="COUNT")
    parser.add_option("-z", "--zone", dest="zone", default=".ru", help="parameter to check for domain zones",
                      metavar="ZONE")
    (options_arr, args) = parser.parse_args()
    return options_arr


# Press the green button in the gutter to run the script.  ConnectionError
if __name__ == '__main__':
    options = parse_arg()
    if options.name:
        for proto in protos:
            response = get_status(proto, options.name, options.zone)
            if response:
                insert_db(options.name + options.zone, proto, response)
        print('Exit 82')
        exit()

    checked = False
    for n in range(2, int(options.count)):
        new_names = generate_names(n)
        print('Generated names with %s letters' % n)
        for site in new_names:
            if not checked:
                if is_last_key(site):
                    checked = True
                continue
            set_last_key(site)
            for proto in protos:
                response = get_status(proto, site, options.zone)
                if response:
                    insert_db(site + options.zone, proto, response)
                    break


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
