# encoding: utf-8
import threading
import time
import gui

class ContentManager(object):
    def __init__(self, func):
        self.func = func
        self.thread = None
        self.objects = []
        self.threads = []


    def _gen_thread_func(self):
        def func():
            while self.objects:
                if gui.misc.STOP_CLICKED:
                    return
                self.func(self.objects.pop(0))

                # thread = threading.Thread(target=self.func, args=(self.objects.pop(0),))
                # thread.start()
                # self.threads.append(thread)

        return func


    def register_objects(self, objects):
        self.objects.extend(objects)

        if gui.misc.STOP_CLICKED:
            print gui.misc.STOP_CLICKED
            return

        if not (self.thread and self.thread.is_alive()):
            self.thread = threading.Thread(target=self._gen_thread_func(), args=())
            self.thread.start()


    def job_done(self):
        return not len(self.objects)


    #def join_all(self):
    #     self.thread.join()

    #     for thread in self.threads:
    #         if gui.misc.STOP_CLICKED:
    #             return

    #         if thread.is_alive():
    #             thread.join()



if __name__ == '__main__':
    def func_mimic(item):
        print '%s in thread' % item
        time.sleep(3)
        print '%s out thread' % item

    content_man = ContentManager(func_mimic)

    content_man.register_objects(range(10))

    time.sleep(3)

    content_man.register_objects(range(10, 20))


