class Fpcs:
    def __init__(self, rate:int) -> None:
        self._rate = rate
        self._need_init = True

    def _init_data(self, node):
        t, v = node[0], node[1]
        self._min_v = v
        self._min_t = t
        self._min_node = node
        self._max_v = v
        self._max_t = t
        self._max_node = node
        self._pre_node = None
        self._pre_max = None
        self._num = 0

    def _step_max(self):
        self._max_node = self._min_node
        self._max_v = self._min_v
        self._max_t = self._min_t
        self._pre_node = self._min_node
        self._pre_max = True
        self._num = 0

    def _step_min(self):
        self._min_node = self._max_node
        self._min_v = self._max_v
        self._min_t = self._max_t
        self._pre_node = self._max_node
        self._pre_max = False
        self._num = 0
    
    def push_data(self, node)->list:
        results = []
        if self._need_init:
            self._need_init = False
            self._init_data(node)
            return results
        t, v = node[0], node[1]
        if v >= self._max_v:
            self._max_v = v
            self._max_t = t
            self._max_node = node
        elif v < self._min_v:
            self._min_v = v
            self._min_t = t
            self._min_node = node
        self._num += 1

        if self._num < self._rate:
            return results
        
        if self._max_t >= self._min_t:
            if self._pre_max is False and self._pre_node[0] != self._min_node[0]:
                results.append(self._pre_node)
            results.append(self._min_node)
            self._step_min()
        else:
            if self._pre_max is True and self._pre_node[0] != self._max_node[0]:
                results.append(self._pre_node)
            results.append(self._max_node)
            self._step_max()
        return results