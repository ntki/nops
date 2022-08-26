import inspect

from lib.targetop import TargetOp, _fill_params


@TargetOp
def t1(progressbar, conf1, conf2=123):
    return (progressbar, conf1, conf2)


@TargetOp
def t2(progressbar, pinproxy, mem, conf1=33):
    return (progressbar, pinproxy, mem, conf1)


def t3(conf1, conf2):
    return conf1, conf2


def t4(conf3=88):
    return conf3



def test_fill_params():
    p2 = inspect.signature(t4).parameters
    assert _fill_params(p2, {}) == {"conf3": 88}
    assert _fill_params(p2, {"t1": 99}) == {"conf3": 88}
    assert _fill_params(p2, {"conf3": 0}) == {"conf3": 0}

    p3 = inspect.signature(t3).parameters
    assert _fill_params(p3, {"conf3": 0}) == {"conf1": None, "conf2": None}


def test_on_function():
    assert t1("_pproxy", "pb", conf1=33) == ("pb", 33, 123)
    assert t2("pp", "pb", "mymem", conf1=888) == ("pb", "pp", "mymem", 888)
    assert t2("pp", "pb", "mymem", conf2=888) == ("pb", "pp", "mymem", 33)


def test_on_late_function():
    t = TargetOp(t4)
    assert t("pp", "pb", conf3=987897) == 987897
    assert t("pp", "pb") == 88
