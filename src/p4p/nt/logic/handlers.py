import logging
from typing import Callable, Optional, OrderedDict

from p4p import Value
from p4p.nt.logic.value_utils import overwrite_unmarked
from p4p.server import ServerOperation
from p4p.server.raw import Handler, SharedPV

logger = logging.getLogger(__name__)


class HandlerError(Exception):
    """
    An error raised by a handler when it is unable to process a request.
    This is used to indicate that the handler has failed and the request should not be processed further.
    """

class CompositeHandler(Handler):
    """
    A handler which may be used to combine (composite) multiple handlers into a single one.
    """

    def __init__(self):
        super().__init__()

        # Name is used purely for logging. Because the name of the PV is stored by
        # the Server and not the PV object associated with this handler we can't
        # determine the name until the first put operation
        self._name = None  # Used purely for logging
        self.rules: OrderedDict[str, Handler] = OrderedDict()

    def __getitem__(self, rule_name: str) -> Optional[Handler]:
        """Allow access to the rules so that parameters such as read_only may be set"""
        return self.rules.get(rule_name)


    def open(self, value: Value):
        pass

    def post(self, pv: SharedPV, value: Value) -> None:
        """
        Handler call by a post operation, requires support from SharedPV derived class
        """
        logger.debug("In handler post()")

        overwrite_unmarked(pv.current().raw, value)

        try:
            for rule_name, rule in self.rules.items():
                logger.debug("Applying rule %s", rule_name)
                rule.post(pv, value)
        except HandlerError as e:
            # Trigger rollback?
            logger.warning("Error in handler %s: %s", self._name, e)
        

    def put(self, pv: SharedPV, op: ServerOperation) -> None:
        """
        Handler triggered by put operations. Note that this has additional information
        about the source of the put such as the IP address of the caller.
        """
        logger.debug("In handler put()")

        overwrite_unmarked(pv.current().raw, op.value().raw)
        try:
            for rule_name, rule in self.rules.items():
                logger.debug("Applying rule %s", rule_name)
                rule.put(pv, op)
        except HandlerError as e:
            op.done(error=repr(e))

        op.done()
