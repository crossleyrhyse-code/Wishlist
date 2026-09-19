from ...adapters.queueit import detect_queue_it
from ...core import engine as ce
from ...adapters.queueit import QueueItActive

def run():
    assert detect_queue_it(location="https://queue.anacondastores.com/?x=1").active
    assert detect_queue_it(location="https://example.queue-it.net/?q=1").active
    assert detect_queue_it(headers={"Location":"https://shop.test/?queueittoken=abc"}).active
    assert detect_queue_it(body="<html>Queue-it waiting room estimated wait time</html>").active
    assert not detect_queue_it(url="https://www.example.com/search?q=awning",
                               body="<html>normal products</html>").active

    original=dict(ce.RETAILERS)
    try:
        def queued(query,limit=20):
            raise QueueItActive("waiting room active")
        ce.RETAILERS={"Anaconda":(queued,RuntimeError)}
        r=ce.compare_across_retailers("270 awning", query="270 awning")
        s=r.retailers[0]
        assert not s.available and s.status=="QUEUE_ACTIVE"
        assert "waiting room" in s.error
    finally:
        ce.RETAILERS=original
    print("QUEUE-IT SAFETY: 8/8 passed")

if __name__=="__main__": run()
