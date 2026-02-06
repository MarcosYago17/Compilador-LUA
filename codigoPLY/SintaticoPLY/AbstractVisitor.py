from abc import abstractmethod, ABCMeta

class AbstractVisitor(metaclass=ABCMeta):

    @abstractmethod
    def visitNumber(self, number):
        pass

    @abstractmethod
    def visitString(self, string):
        pass

    @abstractmethod
    def visitVar(self, var):
        pass

    @abstractmethod
    def visitBoolean(self, boolean):
        pass

    @abstractmethod
    def visitNil(self, nil):
        pass

    @abstractmethod
    def visitUnOp(self, unop):
        pass

    @abstractmethod
    def visitBinOp(self, binop):
        pass

    @abstractmethod
    def visitFunctionCall(self, function_call):
        pass

    @abstractmethod
    def visitAssign(self, assign):
        pass

    @abstractmethod
    def visitFunctionDecl(self, function_decl):
        pass

    @abstractmethod
    def visitWhile(self, while_stmt):
        pass

    @abstractmethod
    def visitFor(self, for_stmt):
        pass

    @abstractmethod
    def visitReturn(self, ret):
        pass

    @abstractmethod
    def visitIf(self, if_stmt):
        pass

    @abstractmethod
    def visitBlock(self, block):
        pass
