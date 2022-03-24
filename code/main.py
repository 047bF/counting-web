from optparse import OptionParser
import string
import itertools
import redis
import datetime
import asyncio
import aiohttp
import traceback


# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
redis = redis.Redis(
     # host='172.21.0.2',
     # host='localhost',
     host='howmanyhost_redis_1',
     port='6379')
     # port='6380')
protos = ['https://', 'http://']
headers = {'user-agent': 'python-requests/2.6.2 CPython/3.4.3 Windows/8'}


def generate_names(count):
    chars = string.ascii_lowercase + string.digits  # "abcdefghijklmnopqrstuvwxyz0123456789"
    for item in itertools.product(chars, repeat=count):
        yield "".join(item)


def get_last_key():
    return str(redis.hget('h_last_key', 'url'), 'cp1252')


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


async def par_run(in_params):
    checked = False
    start_key = get_last_key()
    work_queue = asyncio.Queue()
    for n in range(len(start_key), in_params.count):
        new_names = generate_names(n)
        print('Generated names with %s letters' % n)
        for site in new_names:
            if not checked:
                if is_last_key(site):
                    checked = True
                continue
            else:
                await work_queue.put(site)

        await asyncio.gather(
            asyncio.create_task(check_site("one", in_params, work_queue)),
            asyncio.create_task(check_site("two", in_params, work_queue)),
            asyncio.create_task(check_site("thr", in_params, work_queue)),
            asyncio.create_task(check_site("fou", in_params, work_queue)),
            asyncio.create_task(check_site("fiv", in_params, work_queue)),
            asyncio.create_task(check_site("six", in_params, work_queue)),
        )


async def check_site(name, in_params, queue):
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        while not queue.empty():
            site = await queue.get()
            set_last_key(site)
            for proto in protos:
                response = await get_status(name, session, proto, site, in_params.zone)
                if response:
                    insert_db(site + in_params.zone, proto, response)
                    break


async def get_status(task_name, session, proto, site_name, zone):
    web_url = proto + site_name + zone
    try:
        async with session.get(web_url, headers=headers) as response:
            a_response = await response.text()
            if response.status < 400:
                print('Task %s web site exists: %s' % (task_name, web_url))
                return a_response
    except aiohttp.ClientConnectorError as e:
        None
    except aiohttp.ClientOSError as e:
        None
    except asyncio.TimeoutError as e:
        None
    except aiohttp.ServerDisconnectedError as e:
        None
    except:
        print('ERROR GET URL: ', web_url)
        print(traceback.print_exc())


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

    asyncio.run(par_run(options))



# See PyCharm help at https://www.jetbrains.com/help/pycharm/
