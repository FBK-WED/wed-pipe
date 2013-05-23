""" utility functions for the data_acquisition scripts
"""


def print_error_result(result, label=None):
    """ print the result of calling envoy.run (usually in case of error)
    """
    print "=" * 40
    if label:
        print label
    print '-' * 30

    print 'CMD:'
    print '-' * 30
    print result.command
    print '-' * 30

    print 'OUT:'
    print '-' * 30
    print result.std_out
    print '-' * 30

    print 'ERR:'
    print '-' * 30
    print result.std_err

    if result.history:
        print '-' * 30
        for i, history_result in enumerate(result.history):
            print_error_result(history_result, 'history command {}'.format(i))
    else:
        print '=' * 40
