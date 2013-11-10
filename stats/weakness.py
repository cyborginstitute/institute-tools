from droopy import attr

from utils.structures import AttributeDict

import data


class Weakness(object):
    cache = AttributeDict({'w': None, 'p': None})

    @attr
    def weasel_list(self, d):
        l = []
        for word in d.words:
            if word in data.ww:
                l.append(word)

        w = list(set(l))
        self.cache.w = w
        return w

    @attr
    def weasel_count(self, d):
        if self.cache.w is not None:
            return len(self.cache.w)
        else:
            return len(self.weasel_list(d))

    def passives(self, d):
        p = data.passive_regex.findall(d.text)
        self.cache.p = data.passive_regex.findall(d.text)
        return p

    @attr
    def passive_list(self, d):
        if self.cache.p is None:
            self.passives(d)

        return list(set([' '.join(phrase) for phrase in self.cache.p]))

    @attr
    def passive_count(self, d):
        if self.cache.p is None:
            self.passives(d)

        return len(self.cache.p)
