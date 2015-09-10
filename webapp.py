import tornado.ioloop
import tornado.web

from get_delivery_stats import get_stats


class StatusHandler(tornado.web.RequestHandler):
    def get(self, endpoint):
        try:
            get_stats()
        except Exception as e:
            self.write(e)
            raise
        self.render('throughput.html', title=endpoint)


class HelloHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello!")

def make_app():
    return tornado.web.Application([
        (r"/status/(analysis|delivery)", StatusHandler),
        (r"/hello/", HelloHandler),],
        template_path='templates',
        static_path='.')

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()