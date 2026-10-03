"""The model this application serves, and the code that keeps it honest.

``seeding``, ``device``, ``threads`` and ``runrecord`` are the same modules
the methodology template ships: one seed for every generator, no silent
device fallback, a thread budget checked against the CPUs, and a record of
each training run. ``model`` is the example network and ``predictor`` serves
it inside the web process. Training happens outside the web process; the API
only loads the weights it is given.
"""
