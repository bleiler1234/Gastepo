# -*- coding: utf-8 -*-

from hamcrest import contains_exactly, only_contains, contains_inanyorder
from hamcrest.core.base_matcher import BaseMatcher


def exactly_contains(items):
    return contains_exactly(*items)


def contains_only(items):
    return only_contains(*items)


def inanyorder_contains(items):
    return contains_inanyorder(*items)


class IsContains(BaseMatcher):
    """
    全列表是否包含子列表. EG: [1,2,3] is contains [1,2]
    """

    def __init__(self, sub_list):
        self.sub_list = sub_list

    def _matches(self, total_list):
        self.total_list = total_list
        return set(self.sub_list) <= set(self.total_list)

    def describe_to(self, description):
        description.append_text("total-sequence {} is contains sub-sequence ".format(self.total_list)).append_text(
            self.sub_list)

    def describe_mismatch(self, item, mismatch_description):
        lose_item = set(self.sub_list) - set(self.total_list)
        mismatch_description.append_text("sub-sequence overflow ").append_description_of(list(lose_item))

    def describe_match(self, item, match_description):
        match_description.append_text("was ").append_description_of(item)


def is_contains(sub_list):
    return IsContains(sub_list)


class ContainsIn(BaseMatcher):
    """
    子列表是否存在于全列表中. EG: [1,3] exist in [1,2,3]
    """

    def __init__(self, total_list):
        self.total_list = total_list

    def _matches(self, sub_list):
        self.sub_list = sub_list
        return set(self.sub_list) <= set(self.total_list)

    def describe_to(self, description):
        description.append_text("sub-sequence {} contains in total-sequence ".format(self.sub_list)).append_text(
            self.total_list)

    def describe_mismatch(self, item, mismatch_description):
        lose_item = set(self.sub_list) - set(self.total_list)
        mismatch_description.append_text("sub-sequence overflow ").append_description_of(list(lose_item))

    def describe_match(self, item, match_description):
        match_description.append_text("was ").append_description_of(item)


def contains_in(total_list):
    return ContainsIn(total_list)


class NotContains(BaseMatcher):
    """
      全列表不包含某个子列表. EG: [1,2,3] not contain [4]
      """

    def __init__(self, sub_list):
        self.sub_list = sub_list

    def _matches(self, total_list):
        self.total_list = total_list
        result_set = set(self.total_list) & set(self.sub_list)
        return result_set == set()

    def describe_to(self, description):
        description.append_text("total-sequence {} not contains sub-sequence ".format(self.total_list)).append_text(
            self.sub_list)

    def describe_mismatch(self, item, mismatch_description):
        inter_item = set(self.total_list) & set(self.sub_list)
        mismatch_description.append_text("total-sequence contains ").append_description_of(list(inter_item))

    def describe_match(self, item, match_description):
        match_description.append_text("was ").append_description_of(item)


def not_contains(sub_list):
    return NotContains(sub_list)


if __name__ == '__main__':
    pass
