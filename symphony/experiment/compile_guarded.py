

# class CompileGuarded(object):
#     def __setattr__(self, attr, value):
#         if (not hasattr(self, 'compiled')) or (not self.compiled):
#             object.__setattr__(self, attr, value)
#         else:
#             raise ValueError('Do not mutate an experiment config after it has been compiled by cluster')