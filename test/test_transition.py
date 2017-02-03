from pyabc.transition import NotEnoughParticles, LocalTransition
from pyabc import MultivariateNormalTransition
import pandas as pd
import numpy as np
import scipy as sp
import pytest
from pyabc import GridSearchCV


@pytest.fixture(params=[LocalTransition, MultivariateNormalTransition])
def transition(request):
    return request.param()


def data(n):
    df = pd.DataFrame({"a": np.random.rand(n), "b": np.random.rand(n)})
    w = np.ones(len(df)) / len(df)
    return df, w


def data_single(n):
    df = pd.DataFrame({"a": np.random.rand(n)})
    w = np.ones(len(df)) / len(df)
    return df, w


def test_rvs_return_type(transition):
    df, w = data(20)
    transition.fit(df, w)
    sample = transition.rvs()
    assert (sample.index == pd.Index(["a", "b"])).all()


def test_pdf_return_types(transition):
    df, w = data(20)
    transition.fit(df, w)
    single = transition.pdf(df.iloc[0])
    multiple = transition.pdf(df)
    assert isinstance(single, float)
    assert multiple.shape == (20,)


def test_many_particles_single_par(transition):
    df, w = data_single(20)
    transition.fit(df, w)
    transition.required_nr_samples(.1)


def test_variance_estimate(transition):
    var_list = []
    for n in [20, 250]:
        df, w = data(n)
        transition.fit(df, w)
        var = transition.mean_coefficient_of_variation()
        var_list.append(var)

    assert var_list[0] >= var_list[1]


def test_variance_no_side_effect(transition):
    df, w = data(60)
    transition.fit(df, w)
    # very intrusive test. touches internals of m. not very nice.
    X_orig_id = id(transition.X)
    transition.mean_coefficient_of_variation()  # this has to be called here
    assert id(transition.X) == X_orig_id


def test_particles_no_parameters(transition):
    df = pd.DataFrame(index=[0, 1, 2, 3])
    assert len(df) == 4
    w = np.array([1, 1, 1, 1]) / 4
    transition.fit(df, w)
    with pytest.raises(NotEnoughParticles):
        transition.required_nr_samples(.1)


def test_empty(transition):
    # TODO define proper behavior
    df = pd.DataFrame()
    w = np.array([])
    transition.fit(df, w)
    with pytest.raises(NotEnoughParticles):
        transition.required_nr_samples(.1)


def test_0_particles_fit(transition):
    # TODO define proper behavior
    df, w = data(0)
    with pytest.raises(NotEnoughParticles):
        transition.fit(df, w)


def test_single_particle_fit(transition):
    # TODO define proper behavior
    df, w = data(1)
    transition.fit(df, w)


def test_single_particle_required_nr_samples(transition):
    # TODO define proper behavior
    df, w = data(1)
    transition.fit(df, w)
    transition.required_nr_samples(.1)


def test_two_particles_fit(transition):
    # TODO define proper behavior
    df, w = data(2)
    transition.fit(df, w)


def test_two_particles_required_nr_samples(transition):
    # TODO define proper behavior
    df, w = data(2)
    transition.fit(df, w)
    transition.required_nr_samples(.1)


def test_many_particles(transition):
    df, w = data(20)
    transition.fit(df, w)
    transition.required_nr_samples(.1)


def test_argument_order(transition):
    """
    Dataframes passed to the transition kernels are generated from dicts.
    Order of parameter names is no guaranteed.
    The Transition kernel has to take care of the correct sorting.
    """
    df, w = data(20)
    transition.fit(df, w)
    test = df.iloc[0]
    reversed = test[::-1]
    # works b/c of even nr of parameters
    assert (np.array(test) != np.array(reversed)).all()
    assert transition.pdf(test) == transition.pdf(reversed)


def test_score(transition):
    df, w = data(20)
    transition.fit(df, w)
    transition.score(df, w)  # just call it


def test_grid_search_multivariate_normal():
    m = MultivariateNormalTransition()
    m_grid = GridSearchCV(m, {"scaling": np.logspace(-5, 1.5, 5)})
    df, w = data(20)
    m_grid.fit(df, w)


def test_grid_search_two_samples_multivariate_normal():
    """
    Supposed to run into problems b/c nr splits > then nr_samples
    """
    cv = 5
    m = MultivariateNormalTransition()
    m_grid = GridSearchCV(m, {"scaling": np.logspace(-5, 1.5, 5)}, cv=cv)
    df, w = data(2)
    m_grid.fit(df, w)
    assert m_grid.cv == cv


def test_grid_search_single_sample_multivariate_normal():
    """
    Supposed to run into problems b/c nr splits > then nr_samples
    """
    cv = 5
    m = MultivariateNormalTransition()
    m_grid = GridSearchCV(m, {"scaling": np.logspace(-5, 1.5, 5)}, cv=cv)
    df, w = data(1)
    m_grid.fit(df, w)
    assert m_grid.cv == cv


def test_mean_coefficient_of_variation_sample_not_full_rank(transition):
    """
    This is a test created after I encountered this kind of bug
    """
    n = 13
    df = pd.DataFrame({"a": np.ones(n) + sp.randn(n),
                       "b": np.ones(n)})
    w = np.ones(len(df)) / len(df)
    transition.fit(df, w)
    transition.mean_coefficient_of_variation()
