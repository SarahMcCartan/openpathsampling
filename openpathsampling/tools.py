import sys

__author__ = 'Jan-Hendrik Prinz'


try:
    import IPython
    import IPython.display

    def in_ipynb():
        try:
            ipython = get_ipython()

            import IPython.terminal.interactiveshell
            import ipykernel.zmqshell

            if isinstance(ipython, IPython.terminal.interactiveshell.TerminalInteractiveShell):
                # we are running inside an IPYTHON console
                return False
            elif isinstance(ipython, ipykernel.zmqshell.ZMQInteractiveShell):
                # we run in an IPYTHON notebook
                return True
            else:
                return False
        except NameError:
            # No IPYTHON
            return False
        except:
            # No idea, but we should not fail because of that
            return False

    is_ipynb = in_ipynb()

except ImportError:
    is_ipynb = False

last_output = None


def refresh_output(output_str, print_anyway=True, refresh=True,
                   output_stream=None, ipynb_display_only=False):

    global last_output

    if output_stream is None:
        output_stream = sys.stdout

    if not output_str:
        return

    if refresh:
        if is_ipynb:
            IPython.display.clear_output(wait=True)
        elif output_stream is sys.stdout:
            if last_output is not None:
                lines = len(last_output.split('\n'))
                CURSOR_UP_ONE = '\x1b[1A'
                ERASE_LINE = '\x1b[2K'

                output_stream.write((CURSOR_UP_ONE + ERASE_LINE) * (lines - 1))

            last_output = output_str
    else:
        last_output = None

    output_stream.write(output_str)
    output_stream.flush()


# a little code snippet to wrap strings around for nicer output
# idea found @ http://www.saltycrane.com/blog/2007/09/python-word-wrap-function/

def word_wrap(string, width=80):
    lines = string.split('\n')

    lines = [x.rstrip() for x in lines]
    result = []
    for line in lines:
        while len(line) > width:
            marker = width - 1
            while not line[marker].isspace():
                marker -= 1

            result.append(line[0:marker])
            line = line[marker + 1:]

        result.append(line)
    return '\n'.join(result)


def pretty_print_seconds(seconds, n_labels=0, separator=" "):
    """
    Converts a number of seconds to a readable time string.

    Parameters
    ----------
    seconds : float or int
        number of seconds to represent, gets rounded with int()
    n_labels : int
        number of levels of label to show. For example, if n_labels=1,
        result will show the first of days, hours, minutes, seconds with
        greater than one. This allows you to round, e.g, 1 day 2 hours
        3 minutes 4 seconds to 1 day 2 hours (with n_labels=2). Default
        value of 0 gives all levels. If n_labels is negative, then the last
        value is shown as a decimal, instead of an int, with 2 decimals of
        precision.
    separator : string
        separator between levels of the time decomposition
    on_zero : string
        string to return in the case of 0 seconds
    """
    ordered_keys = ['day', 'hour', 'minute', 'second']
    divisors = {
        'day': 86400,
        'hour': 3600,
        'minute': 60,
        'second': 1
    }

    s = int(seconds)

    parts = {}
    fractional_parts = {}
    for k in ordered_keys:
        fractional_parts[k] = float(s) / divisors[k]
        parts[k], s = divmod(s, divisors[k])

    part_labels = {k: k if parts[k] == 1 else k + "s"
                   for k in ordered_keys}

    decimalize_final = (n_labels < 0)

    first_key = "second"
    for key in ordered_keys:
        if parts[key] > 0:
            first_key = key
            break
    first_key_index = ordered_keys.index(first_key)

    max_labels = len(ordered_keys) - first_key_index
    if n_labels != 0 and abs(n_labels) < max_labels:
        max_labels = abs(n_labels)

    label_count = 0
    output_str = ""
    for key in ordered_keys[first_key_index:]:
        part = parts[key]
        label_str = part_labels[key]
        frac = fractional_parts[key]
        if part > 0 and label_count < max_labels - 1:
            output_str += str(part) + " " + label_str + separator
            label_count += 1
        elif label_count == max_labels - 1:
            if decimalize_final and key != 'second':
                output_str += "%.2f %s" % (frac, key+'s')
            else:
                output_str += str(int(round(frac))) + " " + label_str
            label_count += 1

    return output_str


def progress_string(n_steps_completed, n_steps_total, time_elapsed):
    """
    String to report on simulation progress.

    Assumes that the average time per Monte Carlo/trajectory-level step is
    constant throughout the simulation. These are trajectory-level steps in
    to distinguish them from molecular dynamics (time) steps -- in path
    sampling these are Monte Carlo steps; in order simulations (committor)
    they might not be.

    Parameters
    ----------
    n_steps_completed : int
        number of (Monte Carlo/trajectory-level) steps already completed
    n_steps_total : int
        total number of (Monte Carlo/trajectory-level) step in simulation
    time_elapsed : float-like
        time elapsed in the simulation, in seconds

    Returns
    -------
    str :
        string to output describing simulation progress, including estimated
        time remaining
    """
    try:
        time_per_step = time_elapsed / n_steps_completed
    except ZeroDivisionError:
        return "Starting simulation...\nWorking on first step\n"
    time_to_finish = (n_steps_total - n_steps_completed) * time_per_step
    output_str = (
        "Running for " + pretty_print_seconds(time_elapsed) + " - "
        + "%5.2f seconds per step\n" % (time_per_step)
        + "Estimated time remaining: %s\n" % (
            pretty_print_seconds(time_to_finish, n_labels=-2)
        )
    )
    return output_str
