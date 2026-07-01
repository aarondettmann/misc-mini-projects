#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <math.h>

/* ============================================================
   Utilities
   ============================================================ */

static int extract_vector(PyObject *seq, double *out, Py_ssize_t n) {
  for (Py_ssize_t i = 0; i < n; i++) {
    PyObject *item = PySequence_Fast_GET_ITEM(seq, i);

    if (!PyFloat_Check(item) && !PyLong_Check(item)) {
      PyErr_SetString(PyExc_TypeError,
                      "rhs must return a sequence of real numbers");
      return -1;
    }

    out[i] = PyFloat_AsDouble(item);

    if (PyErr_Occurred()) {
      return -1;
    }
  }
  return 0;
}

static PyObject *build_tuple(const double *x, Py_ssize_t n) {
  /* For scalar states return a float, not a 1-tuple */
  if (n == 1) {
    return PyFloat_FromDouble(x[0]);
  }

  PyObject *t = PyTuple_New(n);
  if (!t)
    return NULL;

  for (Py_ssize_t i = 0; i < n; i++) {
    PyObject *v = PyFloat_FromDouble(x[i]);
    if (!v) {
      Py_DECREF(t);
      return NULL;
    }
    PyTuple_SET_ITEM(t, i, v);
  }
  return t;
}

static int call_rhs(PyObject *rhs, PyObject *t_obj, PyObject *y_obj,
                    PyObject **out_seq, Py_ssize_t expected_n) {
  PyObject *res = PyObject_CallFunctionObjArgs(rhs, t_obj, y_obj, NULL);
  if (!res)
    return -1;

  /* If a scalar is expected, accept numeric returns and wrap them */
  if (expected_n == 1 && (PyFloat_Check(res) || PyLong_Check(res))) {
    double dv = PyFloat_AsDouble(res);
    if (PyErr_Occurred()) {
      Py_DECREF(res);
      return -1;
    }
    PyObject *seq = PyTuple_New(1);
    if (!seq) {
      Py_DECREF(res);
      return -1;
    }
    PyObject *item = PyFloat_FromDouble(dv);
    if (!item) {
      Py_DECREF(seq);
      Py_DECREF(res);
      return -1;
    }
    PyTuple_SET_ITEM(seq, 0, item);
    Py_DECREF(res);
    *out_seq = seq;
    return 0;
  }

  PyObject *seq =
      PySequence_Fast(res, "rhs must return a sequence of real numbers");

  Py_DECREF(res);

  if (!seq)
    return -1;

  *out_seq = seq;
  return 0;
}

/* ============================================================
   RK4 stage helper (removes repetition)
   ============================================================ */

static int rk4_stage(PyObject *rhs, double t, const double *y_in,
                     const double *k_in, double *y_tmp, double *out_k, double h,
                     double scale, Py_ssize_t n) {
  PyObject *t_obj = PyFloat_FromDouble(t);
  if (!t_obj)
    return -1;

  for (Py_ssize_t i = 0; i < n; i++) {
    if (k_in) {
      y_tmp[i] = y_in[i] + scale * h * k_in[i];
    } else {
      y_tmp[i] = y_in[i];
    }
  }

  PyObject *y_obj = build_tuple(y_tmp, n);
  if (!y_obj) {
    Py_DECREF(t_obj);
    return -1;
  }

  PyObject *seq;
  if (call_rhs(rhs, t_obj, y_obj, &seq, n) < 0) {
    Py_DECREF(t_obj);
    Py_DECREF(y_obj);
    return -1;
  }

  Py_DECREF(t_obj);
  Py_DECREF(y_obj);

  int ok = extract_vector(seq, out_k, n);
  Py_DECREF(seq);

  return ok;
}

/* ============================================================
   Main integrator
   ============================================================ */

static PyObject *rk4_integrate(PyObject *self, PyObject *args) {
  PyObject *rhs;
  PyObject *y0_obj;
  double t0, h;
  Py_ssize_t n_steps;

  (void)self;

  if (!PyArg_ParseTuple(args, "OdOdn", &rhs, &t0, &y0_obj, &h, &n_steps)) {
    return NULL;
  }

  if (!PyCallable_Check(rhs)) {
    PyErr_SetString(PyExc_TypeError, "rhs must be callable");
    return NULL;
  }

  if (n_steps <= 0) {
    PyErr_SetString(PyExc_ValueError, "n_steps must be > 0");
    return NULL;
  }

  if (!isfinite(h) || h == 0.0) {
    PyErr_SetString(PyExc_ValueError, "h must be finite and non-zero");
    return NULL;
  }

  /* --------------------------------------------------------
     State normalization (scalar or vector)
     -------------------------------------------------------- */

  Py_ssize_t n;
  int is_scalar = 0;
  PyObject *y0_seq = NULL;

  if (PyFloat_Check(y0_obj) || PyLong_Check(y0_obj)) {
    is_scalar = 1;
    n = 1;
  } else {
    y0_seq = PySequence_Fast(y0_obj, "y0 must be float or sequence");
    if (!y0_seq)
      return NULL;

    n = PySequence_Fast_GET_SIZE(y0_seq);

    if (n <= 0) {
      Py_DECREF(y0_seq);
      PyErr_SetString(PyExc_ValueError, "y0 must not be empty");
      return NULL;
    }
  }

  /* --------------------------------------------------------
     Allocate buffers
     -------------------------------------------------------- */

  double *y = PyMem_Malloc(sizeof(double) * n);
  double *tmp = PyMem_Malloc(sizeof(double) * n);
  double *k1 = PyMem_Malloc(sizeof(double) * n);
  double *k2 = PyMem_Malloc(sizeof(double) * n);
  double *k3 = PyMem_Malloc(sizeof(double) * n);
  double *k4 = PyMem_Malloc(sizeof(double) * n);

  if (!y || !tmp || !k1 || !k2 || !k3 || !k4) {
    PyErr_NoMemory();
    goto fail;
  }

  /* --------------------------------------------------------
     Initialize state
     -------------------------------------------------------- */

  if (is_scalar) {
    y[0] = PyFloat_AsDouble(y0_obj);
    if (PyErr_Occurred())
      goto fail;
  } else {
    for (Py_ssize_t i = 0; i < n; i++) {
      PyObject *item = PySequence_Fast_GET_ITEM(y0_seq, i);
      y[i] = PyFloat_AsDouble(item);
      if (PyErr_Occurred())
        goto fail;
    }
    Py_DECREF(y0_seq);
  }

  /* --------------------------------------------------------
     Output containers
     -------------------------------------------------------- */

  PyObject *times = PyList_New(n_steps + 1);
  PyObject *states = PyList_New(n_steps + 1);

  if (!times || !states)
    goto fail;

  double t = t0;

  PyList_SET_ITEM(times, 0, PyFloat_FromDouble(t));
  PyList_SET_ITEM(states, 0, build_tuple(y, n));

  const double h2 = 0.5 * h;
  const double h6 = h / 6.0;

  /* --------------------------------------------------------
     RK4 loop
     -------------------------------------------------------- */

  for (Py_ssize_t step = 0; step < n_steps; step++) {
    if (rk4_stage(rhs, t, y, NULL, tmp, k1, h, 0.0, n) < 0)
      goto fail;
    if (rk4_stage(rhs, t + h2, y, k1, tmp, k2, h, 0.5, n) < 0)
      goto fail;
    if (rk4_stage(rhs, t + h2, y, k2, tmp, k3, h, 0.5, n) < 0)
      goto fail;
    if (rk4_stage(rhs, t + h, y, k3, tmp, k4, h, 1.0, n) < 0)
      goto fail;

    for (Py_ssize_t i = 0; i < n; i++) {
      y[i] += h6 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]);
    }

    t += h;

    PyList_SET_ITEM(times, step + 1, PyFloat_FromDouble(t));
    PyList_SET_ITEM(states, step + 1, build_tuple(y, n));
  }

  /* --------------------------------------------------------
     Cleanup success
     -------------------------------------------------------- */

  PyMem_Free(y);
  PyMem_Free(tmp);
  PyMem_Free(k1);
  PyMem_Free(k2);
  PyMem_Free(k3);
  PyMem_Free(k4);

  return Py_BuildValue("NN", times, states);

/* ------------------------------------------------------------
   Failure cleanup
   ------------------------------------------------------------ */
fail:
  Py_XDECREF(y0_seq);
  Py_XDECREF(times);
  Py_XDECREF(states);

  PyMem_Free(y);
  PyMem_Free(tmp);
  PyMem_Free(k1);
  PyMem_Free(k2);
  PyMem_Free(k3);
  PyMem_Free(k4);

  return NULL;
}

/* ============================================================
   Module definition
   ============================================================ */

static PyMethodDef rk4_methods[] = {{"integrate", rk4_integrate, METH_VARARGS,
                                     "Integrate ODE using classical RK4."},
                                    {NULL, NULL, 0, NULL}};

static struct PyModuleDef rk4_module = {PyModuleDef_HEAD_INIT, "_rk4",
                                        "Pure C RK4 integrator core", -1,
                                        rk4_methods};

PyMODINIT_FUNC PyInit__rk4(void) { return PyModule_Create(&rk4_module); }
