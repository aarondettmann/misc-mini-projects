#define PY_SSIZE_T_CLEAN
#include <Python.h>

static int set_list_item_float(PyObject *list_obj, Py_ssize_t index, double value) {
    PyObject *number = PyFloat_FromDouble(value);
    if (number == NULL) {
        return -1;
    }
    PyList_SET_ITEM(list_obj, index, number);
    return 0;
}

static PyObject *build_state_tuple(const double *state, Py_ssize_t size) {
    Py_ssize_t i = 0;
    PyObject *tuple_obj = PyTuple_New(size);
    if (tuple_obj == NULL) {
        return NULL;
    }

    for (i = 0; i < size; ++i) {
        PyObject *value_obj = PyFloat_FromDouble(state[i]);
        if (value_obj == NULL) {
            Py_DECREF(tuple_obj);
            return NULL;
        }
        PyTuple_SET_ITEM(tuple_obj, i, value_obj);
    }

    return tuple_obj;
}

/* Call the user-supplied RHS for a scalar state and coerce the result to double. */
static int call_rhs_scalar(PyObject *rhs, double t, double y, double *out_value) {
    PyObject *t_obj = NULL;
    PyObject *y_obj = NULL;
    PyObject *rhs_result = NULL;
    double result_value = 0.0;

    t_obj = PyFloat_FromDouble(t);
    if (t_obj == NULL) {
        return -1;
    }
    y_obj = PyFloat_FromDouble(y);
    if (y_obj == NULL) {
        Py_DECREF(t_obj);
        return -1;
    }

    rhs_result = PyObject_CallFunctionObjArgs(rhs, t_obj, y_obj, NULL);
    Py_DECREF(t_obj);
    Py_DECREF(y_obj);

    if (rhs_result == NULL) {
        return -1;
    }

    result_value = PyFloat_AsDouble(rhs_result);
    Py_DECREF(rhs_result);
    if (PyErr_Occurred()) {
        return -1;
    }

    *out_value = result_value;
    return 0;
}

/* Call the user-supplied RHS for a vector state and validate the returned shape. */
static int call_rhs_vector(PyObject *rhs, double t, const double *state, Py_ssize_t size, double *out_values) {
    Py_ssize_t i = 0;
    PyObject *t_obj = NULL;
    PyObject *state_obj = NULL;
    PyObject *rhs_result = NULL;
    PyObject *rhs_seq = NULL;

    t_obj = PyFloat_FromDouble(t);
    if (t_obj == NULL) {
        return -1;
    }
    state_obj = build_state_tuple(state, size);
    if (state_obj == NULL) {
        Py_DECREF(t_obj);
        return -1;
    }

    rhs_result = PyObject_CallFunctionObjArgs(rhs, t_obj, state_obj, NULL);
    Py_DECREF(t_obj);
    Py_DECREF(state_obj);
    if (rhs_result == NULL) {
        return -1;
    }

    rhs_seq = PySequence_Fast(
        rhs_result,
        "rhs must return a sequence with the same length as y"
    );
    Py_DECREF(rhs_result);
    if (rhs_seq == NULL) {
        return -1;
    }

    if (PySequence_Fast_GET_SIZE(rhs_seq) != size) {
        PyErr_SetString(PyExc_ValueError, "rhs return length must match y dimension");
        Py_DECREF(rhs_seq);
        return -1;
    }

    for (i = 0; i < size; ++i) {
        PyObject *component = PySequence_Fast_GET_ITEM(rhs_seq, i);
        out_values[i] = PyFloat_AsDouble(component);
        if (PyErr_Occurred()) {
            Py_DECREF(rhs_seq);
            return -1;
        }
    }

    Py_DECREF(rhs_seq);
    return 0;
}

static PyObject *integrate_scalar(PyObject *rhs, double t0, double y0, double h, Py_ssize_t n_steps) {
    Py_ssize_t step = 0;
    double t = t0;
    double y = y0;
    PyObject *times = NULL;
    PyObject *states = NULL;

    times = PyList_New(n_steps + 1);
    if (times == NULL) {
        return NULL;
    }
    states = PyList_New(n_steps + 1);
    if (states == NULL) {
        Py_DECREF(times);
        return NULL;
    }

    if (set_list_item_float(times, 0, t) < 0 || set_list_item_float(states, 0, y) < 0) {
        Py_DECREF(times);
        Py_DECREF(states);
        return NULL;
    }

    for (step = 0; step < n_steps; ++step) {
        double k1 = 0.0;
        double k2 = 0.0;
        double k3 = 0.0;
        double k4 = 0.0;

        if (call_rhs_scalar(rhs, t, y, &k1) < 0) {
            Py_DECREF(times);
            Py_DECREF(states);
            return NULL;
        }
        if (call_rhs_scalar(rhs, t + 0.5 * h, y + 0.5 * h * k1, &k2) < 0) {
            Py_DECREF(times);
            Py_DECREF(states);
            return NULL;
        }
        if (call_rhs_scalar(rhs, t + 0.5 * h, y + 0.5 * h * k2, &k3) < 0) {
            Py_DECREF(times);
            Py_DECREF(states);
            return NULL;
        }
        if (call_rhs_scalar(rhs, t + h, y + h * k3, &k4) < 0) {
            Py_DECREF(times);
            Py_DECREF(states);
            return NULL;
        }

        y += (h / 6.0) * (k1 + (2.0 * k2) + (2.0 * k3) + k4);
        t += h;

        if (set_list_item_float(times, step + 1, t) < 0 || set_list_item_float(states, step + 1, y) < 0) {
            Py_DECREF(times);
            Py_DECREF(states);
            return NULL;
        }
    }

    return Py_BuildValue("NN", times, states);
}

static PyObject *integrate_vector(PyObject *rhs, double t0, PyObject *y0_obj, double h, Py_ssize_t n_steps) {
    Py_ssize_t i = 0;
    Py_ssize_t step = 0;
    Py_ssize_t dimension = 0;
    double t = t0;
    double *y = NULL;
    double *ytmp = NULL;
    double *k1 = NULL;
    double *k2 = NULL;
    double *k3 = NULL;
    double *k4 = NULL;
    PyObject *times = NULL;
    PyObject *states = NULL;
    PyObject *y0_seq = NULL;

    y0_seq = PySequence_Fast(y0_obj, "y0 must be a sequence of real numbers");
    if (y0_seq == NULL) {
        return NULL;
    }

    dimension = PySequence_Fast_GET_SIZE(y0_seq);
    if (dimension <= 0) {
        Py_DECREF(y0_seq);
        PyErr_SetString(PyExc_ValueError, "y0 sequence must not be empty");
        return NULL;
    }

    y = PyMem_Malloc(sizeof(double) * (size_t)dimension);
    ytmp = PyMem_Malloc(sizeof(double) * (size_t)dimension);
    k1 = PyMem_Malloc(sizeof(double) * (size_t)dimension);
    k2 = PyMem_Malloc(sizeof(double) * (size_t)dimension);
    k3 = PyMem_Malloc(sizeof(double) * (size_t)dimension);
    k4 = PyMem_Malloc(sizeof(double) * (size_t)dimension);
    if (y == NULL || ytmp == NULL || k1 == NULL || k2 == NULL || k3 == NULL || k4 == NULL) {
        Py_DECREF(y0_seq);
        PyMem_Free(y);
        PyMem_Free(ytmp);
        PyMem_Free(k1);
        PyMem_Free(k2);
        PyMem_Free(k3);
        PyMem_Free(k4);
        PyErr_NoMemory();
        return NULL;
    }

    for (i = 0; i < dimension; ++i) {
        PyObject *component = PySequence_Fast_GET_ITEM(y0_seq, i);
        y[i] = PyFloat_AsDouble(component);
        if (PyErr_Occurred()) {
            Py_DECREF(y0_seq);
            PyMem_Free(y);
            PyMem_Free(ytmp);
            PyMem_Free(k1);
            PyMem_Free(k2);
            PyMem_Free(k3);
            PyMem_Free(k4);
            return NULL;
        }
    }
    Py_DECREF(y0_seq);

    times = PyList_New(n_steps + 1);
    if (times == NULL) {
        PyMem_Free(y);
        PyMem_Free(ytmp);
        PyMem_Free(k1);
        PyMem_Free(k2);
        PyMem_Free(k3);
        PyMem_Free(k4);
        return NULL;
    }
    states = PyList_New(n_steps + 1);
    if (states == NULL) {
        Py_DECREF(times);
        PyMem_Free(y);
        PyMem_Free(ytmp);
        PyMem_Free(k1);
        PyMem_Free(k2);
        PyMem_Free(k3);
        PyMem_Free(k4);
        return NULL;
    }

    if (set_list_item_float(times, 0, t) < 0) {
        Py_DECREF(times);
        Py_DECREF(states);
        PyMem_Free(y);
        PyMem_Free(ytmp);
        PyMem_Free(k1);
        PyMem_Free(k2);
        PyMem_Free(k3);
        PyMem_Free(k4);
        return NULL;
    }
    {
        PyObject *initial_state = build_state_tuple(y, dimension);
        if (initial_state == NULL) {
            Py_DECREF(times);
            Py_DECREF(states);
            PyMem_Free(y);
            PyMem_Free(ytmp);
            PyMem_Free(k1);
            PyMem_Free(k2);
            PyMem_Free(k3);
            PyMem_Free(k4);
            return NULL;
        }
        PyList_SET_ITEM(states, 0, initial_state);
    }

    for (step = 0; step < n_steps; ++step) {
        if (call_rhs_vector(rhs, t, y, dimension, k1) < 0) {
            Py_DECREF(times);
            Py_DECREF(states);
            PyMem_Free(y);
            PyMem_Free(ytmp);
            PyMem_Free(k1);
            PyMem_Free(k2);
            PyMem_Free(k3);
            PyMem_Free(k4);
            return NULL;
        }

        /* Stage values are computed into a temporary buffer to keep y immutable until the update. */
        for (i = 0; i < dimension; ++i) {
            ytmp[i] = y[i] + 0.5 * h * k1[i];
        }
        if (call_rhs_vector(rhs, t + 0.5 * h, ytmp, dimension, k2) < 0) {
            Py_DECREF(times);
            Py_DECREF(states);
            PyMem_Free(y);
            PyMem_Free(ytmp);
            PyMem_Free(k1);
            PyMem_Free(k2);
            PyMem_Free(k3);
            PyMem_Free(k4);
            return NULL;
        }

        for (i = 0; i < dimension; ++i) {
            ytmp[i] = y[i] + 0.5 * h * k2[i];
        }
        if (call_rhs_vector(rhs, t + 0.5 * h, ytmp, dimension, k3) < 0) {
            Py_DECREF(times);
            Py_DECREF(states);
            PyMem_Free(y);
            PyMem_Free(ytmp);
            PyMem_Free(k1);
            PyMem_Free(k2);
            PyMem_Free(k3);
            PyMem_Free(k4);
            return NULL;
        }

        for (i = 0; i < dimension; ++i) {
            ytmp[i] = y[i] + h * k3[i];
        }
        if (call_rhs_vector(rhs, t + h, ytmp, dimension, k4) < 0) {
            Py_DECREF(times);
            Py_DECREF(states);
            PyMem_Free(y);
            PyMem_Free(ytmp);
            PyMem_Free(k1);
            PyMem_Free(k2);
            PyMem_Free(k3);
            PyMem_Free(k4);
            return NULL;
        }

        for (i = 0; i < dimension; ++i) {
            y[i] += (h / 6.0) * (k1[i] + (2.0 * k2[i]) + (2.0 * k3[i]) + k4[i]);
        }
        t += h;

        if (set_list_item_float(times, step + 1, t) < 0) {
            Py_DECREF(times);
            Py_DECREF(states);
            PyMem_Free(y);
            PyMem_Free(ytmp);
            PyMem_Free(k1);
            PyMem_Free(k2);
            PyMem_Free(k3);
            PyMem_Free(k4);
            return NULL;
        }
        {
            PyObject *state_obj = build_state_tuple(y, dimension);
            if (state_obj == NULL) {
                Py_DECREF(times);
                Py_DECREF(states);
                PyMem_Free(y);
                PyMem_Free(ytmp);
                PyMem_Free(k1);
                PyMem_Free(k2);
                PyMem_Free(k3);
                PyMem_Free(k4);
                return NULL;
            }
            PyList_SET_ITEM(states, step + 1, state_obj);
        }
    }

    PyMem_Free(y);
    PyMem_Free(ytmp);
    PyMem_Free(k1);
    PyMem_Free(k2);
    PyMem_Free(k3);
    PyMem_Free(k4);

    return Py_BuildValue("NN", times, states);
}

static PyObject *rk4_integrate(PyObject *self, PyObject *args) {
    PyObject *rhs = NULL;
    PyObject *y0_obj = NULL;
    double t0 = 0.0;
    double h = 0.0;
    Py_ssize_t n_steps = 0;

    (void)self;

    if (!PyArg_ParseTuple(args, "OdOdn:integrate", &rhs, &t0, &y0_obj, &h, &n_steps)) {
        return NULL;
    }
    if (!PyCallable_Check(rhs)) {
        PyErr_SetString(PyExc_TypeError, "rhs must be callable");
        return NULL;
    }
    if (n_steps <= 0) {
        PyErr_SetString(PyExc_ValueError, "n_steps must be greater than 0");
        return NULL;
    }
    if (h == 0.0) {
        PyErr_SetString(PyExc_ValueError, "h must be non-zero");
        return NULL;
    }

    if (PySequence_Check(y0_obj) && !PyUnicode_Check(y0_obj) && !PyBytes_Check(y0_obj)) {
        return integrate_vector(rhs, t0, y0_obj, h, n_steps);
    }

    {
        double y0 = PyFloat_AsDouble(y0_obj);
        if (PyErr_Occurred()) {
            return NULL;
        }
        return integrate_scalar(rhs, t0, y0, h, n_steps);
    }
}

static PyMethodDef rk4_methods[] = {
    {
        "integrate",
        rk4_integrate,
        METH_VARARGS,
        "Integrate an ODE using fixed-step RK4.",
    },
    {NULL, NULL, 0, NULL},
};

static struct PyModuleDef rk4_module = {
    PyModuleDef_HEAD_INIT,
    "_rk4",
    "C-extension RK4 core.",
    -1,
    rk4_methods,
};

PyMODINIT_FUNC PyInit__rk4(void) {
    return PyModule_Create(&rk4_module);
}
