__all__ = [ 'dot', 'where', 'sum', 'broadcast_to', 'hstack', 'stack', 'sparsesum', 'branch']

from sparsegrad import impl
import sparsegrad.impl.sparsevec as impl_sparsevec
from sparsegrad.impl.multipledispatch import dispatch, GenericFunction
from . import routing
import numpy as np

dot = GenericFunction('dot')
dot.add((object, object), impl.dot_)

where = GenericFunction('where')
where.add((object, object, object), np.where)

sum = GenericFunction('sum')
sum.add((object,), np.sum)

broadcast_to = GenericFunction('broadcast_to')
broadcast_to.add((object, object), np.broadcast_to)

def hstack(arrays):
    "Generalized version of numpy.hstack"
    return routing.hstack(routing.find_implementation(arrays), arrays)

def stack(*arrays):
    "Alias for hstack, taking arrays as separate arguments"
    return hstack(arrays)

def sparsesum(terms, **kwargs):
    "Generalized version of sparsesum"
    impl = routing.find_implementation((a.v for a in terms), default=impl_sparsevec)
    return routing.sparsesum(impl, terms, **kwargs)

@dispatch(object, object, object)
def branch(cond, iftrue, iffalse):
    """
    Branch execution

    Note that, in some cases (propagation of sparsity pattern), both branches can executed
    more than once.

    Parameters:
    -----------
    cond : bool vector
        Condition
    iftrue : callable(idx)
        Function called to evaluate elements with indices idx, where cond is True
    iffalse : callable(idx)
        Function called to evaluate elements with indices idx, where cond is False

    """

    def _branch(cond, iftrue, iffalse):
        if not cond.shape:
            if cond:
                return iftrue(None)
            return iffalse(None)
        n = len(cond)
        r = np.arange(len(cond))
        ixtrue = r[cond]
        ixfalse = r[np.logical_not(cond)]
        vtrue = impl_sparsevec.sparsevec(
            n, ixtrue, broadcast_to(
                iftrue(ixtrue), ixtrue.shape))
        vfalse = impl_sparsevec.sparsevec(
            n, ixfalse, broadcast_to(
                iffalse(ixfalse), ixfalse.shape))
        return sparsesum([vtrue, vfalse])
    value = _branch(cond, iftrue, iffalse)
    return value
