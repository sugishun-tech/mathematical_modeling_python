import itertools
from types import SimpleNamespace
import numpy as np
import pytest
from scipy.optimize import linprog
from modeling.optimization import newton_scalar,newton_system,sensitivity,check_solution,binary_knapsack,branch_and_bound
from modeling.dynamics import iterate_map,euler,stability,docking_matrix,iterate_linear,competition_rhs,simulate_battle
from modeling.probability import stationary_distribution,birth_death_stationary,wilson_interval,has_run,run_probability,rainy_simulation,inventory_transition,inverse_exponential,first_passage
from modeling.particles import centered_pareto,track_particles,concentration_interval,last_threshold_bracket
from modeling.regression import ar1_forecast,corrected_deadtime_rate
from modeling.simulation import docking_trial,triangular_wind

@pytest.mark.parametrize('target',[.001,.25,2.,10.,100.])
def test_newton_roots(target):
    result=newton_scalar(lambda x:x*x-target,lambda x:2*x,max(1,target))
    assert np.isclose(result.root[0],np.sqrt(target),atol=1e-8)
    assert result.residuals[-1]<=1e-10
    assert np.all(np.diff(result.residuals)<0)

def test_newton_system_and_domain():
    result=newton_system(lambda x:[x[0]**2-2,x[1]**2-3],lambda x:np.diag(2*x),[1.,1.],domain=lambda x:np.all(x>0))
    assert np.allclose(result.root,np.sqrt([2,3]))
    with pytest.raises(ValueError):newton_system(lambda x:x,lambda x:np.eye(1),[-1],domain=lambda x:np.all(x>0))
    with pytest.raises(RuntimeError):newton_scalar(lambda x:x*x+1,lambda x:2*x,0)
    with pytest.raises(RuntimeError):newton_scalar(lambda x:1.,lambda x:1.,0)
    with pytest.raises(ValueError):newton_scalar(lambda x:x,lambda x:1,0,tolerance=0)

@pytest.mark.parametrize('power',[-3,-1,1,2,4])
@pytest.mark.parametrize('a',[.1,1.,10.])
def test_sensitivity(power,a):
    assert np.isclose(sensitivity(lambda x:x**power,a),power,rtol=1e-6)

@pytest.mark.parametrize('f,a',[(lambda x:x,0),(lambda x:0.,1)])
def test_undefined_elasticity(f,a):
    with pytest.raises(ValueError):sensitivity(f,a)

def test_solution_checks():
    with pytest.raises(RuntimeError):check_solution(SimpleNamespace(success=False,x=None,message='infeasible'))
    result=SimpleNamespace(success=True,x=np.array([2.,1.]),fun=3.)
    check_solution(result,A_ub=[[1,1]],b_ub=[3],lower=0,integral=True)
    with pytest.raises(AssertionError):check_solution(result,A_ub=[[1,1]],b_ub=[2])
    with pytest.raises(AssertionError):check_solution(result,A_eq=[[1,1]],b_eq=[2])
    with pytest.raises(AssertionError):check_solution(SimpleNamespace(success=True,x=np.array([.5]),fun=.5),integral=True)

def test_farm_corrected_coefficients_and_all_scenarios():
    acre_A=np.array([[3,1,1.5],[.8,.2,.3]])
    A=np.vstack([np.hstack([120*acre_A,25*acre_A]),[1,1,1,0,0,0],[0,0,0,1,1,1]])
    c=np.array([48000,24000,30000,10000,5000,6250.])
    for water,expected in [(950,156250),(1000,162250),(1100,172000)]:
        b=np.array([water,300,5,1])
        value,point,log=branch_and_bound(c,A,b,[5,5,5,1,1,1])
        enumeration=[]
        for large in itertools.product(range(6),repeat=3):
            for small in itertools.product(range(2),repeat=3):
                x=np.array(large+small)
                if np.all(A@x<=b+1e-10):enumeration.append(c@x)
        assert value==max(enumeration)==expected
        assert np.all(A@point<=b+1e-10)
    relaxation=linprog(-c,A_ub=A,b_ub=[1000,300,5,1],bounds=(0,None),method='highs')
    check_solution(relaxation);assert np.isclose(-relaxation.fun,162500)

def test_binary_ties_and_trucks():
    value,points=binary_knapsack([1,1],[1,1],1)
    assert value==1 and len(points)==2
    assert binary_knapsack([100,360,400,200,640],[1,1,2,1,2],3)[0]==1000
    with pytest.raises(ValueError):binary_knapsack([1],[1],-1)

def test_map_simultaneous_and_initial_stop():
    result=iterate_map(lambda n,x:[x[1],x[0]],[1,2],3)
    assert np.array_equal(result.states,[[1,2],[2,1],[1,2],[2,1]])
    stop=iterate_map(lambda n,x:1/0,[0],10,stop=lambda n,x:'done')
    assert len(stop.states)==1 and stop.stop_reason=='done'
    result=iterate_map(lambda n,x:x*2,[1],100,max_norm=5)
    assert result.stop_reason=='norm limit' and result.states[-1,0]==8

@pytest.mark.parametrize('h',[.1,.5,1.,1.5,2.,2.5])
def test_euler_closed_form(h):
    times,x=euler(lambda t,x:-x,0,[1],h*10,10)
    assert np.allclose(x[:,0],(1-h)**np.arange(11))
    assert times[0]==0 and times[-1]==10*h

@pytest.mark.parametrize('steps',[0,-1,1.5,True])
def test_bad_euler_steps(steps):
    with pytest.raises(ValueError):euler(lambda t,x:-x,0,[1],1,steps)

@pytest.mark.parametrize('value,discrete,expected',[(-1,False,'asymptotically'),(1,False,'unstable'),(0,False,'inconclusive'),(.5,True,'asymptotically'),(1,True,'inconclusive'),(-1,True,'inconclusive'),(1.2,True,'unstable')])
def test_stability(value,discrete,expected):
    assert stability([[value]],discrete=discrete)[0].startswith(expected)

def test_docking_linear():
    A=docking_matrix(.02);initial=np.array([50.,50.])
    assert np.allclose(iterate_linear(A,initial,30)[-1],np.linalg.matrix_power(A,30)@initial)
    assert stability(docking_matrix(.2),discrete=True)[0].startswith('inconclusive')

def test_competition_axes_and_equilibrium():
    rhs=competition_rhs([.05,.08],[150000,400000],[1e-7,1e-7])
    assert rhs(0,[0,70_000])[0]==0 and rhs(0,[5000,0])[1]==0
    eq=np.linalg.solve([[.05/150000,1e-7],[1e-7,.08/400000]],[.05,.08])
    assert np.linalg.norm(rhs(0,eq))<1e-9

def test_battle_first_step_and_horizon():
    frame,status=simulate_battle(1,max_hours=1)
    assert status=='horizon reached'
    assert np.allclose(frame.iloc[1][['red','blue']],[4.85,1.7])
    assert simulate_battle(6,max_hours=168)[1]=='blue'

def test_stationary_and_periodic():
    p=stationary_distribution([[.5,.5],[.25,.75]])
    assert np.allclose(p,[1/3,2/3])
    assert np.allclose(stationary_distribution([[0,1],[1,0]]),[.5,.5])
    assert np.allclose(stationary_distribution([[-2,2],[1,-1]],continuous=True),[1/3,2/3])

@pytest.mark.parametrize('matrix,ct',[(np.eye(2),False),([[.5,.6],[1,0]],False),([[-1,2],[1,-1]],True),([[-.2,1.2],[0,1]],False)])
def test_invalid_stationary(matrix,ct):
    with pytest.raises(ValueError):stationary_distribution(matrix,continuous=ct)

@pytest.mark.parametrize('arrival,service,capacity',[(0,1,10),(1,1,3),(.5,1,100),(10,1,30),(1e100,1,200),(1,1,0)])
def test_birth_death(arrival,service,capacity):
    p=birth_death_stationary(arrival,service,capacity)
    assert len(p)==capacity+1 and np.all(p>=0) and np.isclose(p.sum(),1)
    if arrival==service:assert np.allclose(p,np.ones(capacity+1)/(capacity+1))
    if arrival==0:assert p[0]==1

@pytest.mark.parametrize('n,k',[(1,0),(1,1),(10,0),(10,10),(100,50)])
def test_wilson(n,k):
    lo,hi=wilson_interval(k,n)
    assert 0<=lo<=k/n<=hi<=1

@pytest.mark.parametrize('days',range(0,9))
@pytest.mark.parametrize('p',[0.,.2,.5,.9,1.])
def test_exact_run_enumeration(days,p):
    brute=sum(p**sum(row)*(1-p)**(days-sum(row)) for row in itertools.product([0,1],repeat=days) if has_run(row,3))
    assert np.isclose(run_probability(days,3,p),brute,atol=1e-12)

def test_rain_simulation_extremes():
    rng=np.random.default_rng(1)
    assert rainy_simulation(rng,100,p=1).all()
    assert not rainy_simulation(rng,100,p=0).any()
    assert not rainy_simulation(rng,100,days=2,run_length=3).any()

@pytest.mark.parametrize('rate',[0.,.1,1.,10.])
@pytest.mark.parametrize('policy',[1,2,3])
def test_inventory_rows(rate,policy):
    P=inventory_transition(rate,3,policy)
    assert np.all(P>=0) and np.allclose(P.sum(1),1)

def test_inverse_and_passage():
    assert inverse_exponential(0,1)==0
    assert np.isclose(inverse_exponential(.5,2),np.log(2)/2)
    with pytest.raises(ValueError):inverse_exponential(1,1)
    class FakeRNG:
        def exponential(self,scale):return 25.
    assert first_passage(FakeRNG(),threshold=100)==4
    with pytest.raises(RuntimeError):first_passage(FakeRNG(),threshold=100,max_steps=3)

def test_particle_drift_and_mass():
    result=track_particles(np.random.default_rng(1),100,2,10,lambda t,x:3.,lambda rng,n,dt:np.zeros(n),window=(5,7),snapshot_steps=[0,10])
    assert np.allclose(result.final_positions,6)
    assert result.counts[-1]==100 and len(result.snapshots)==2
    point,lo,hi=concentration_interval([0,50,100],100,540,10)
    assert np.allclose(point,[0,27,54]) and np.all(lo<=point) and np.all(hi>=point)
    assert last_threshold_bracket([1,2,3],[0,3,1],2)==(2.,3.,'last sampled downcrossing (not a safety guarantee)')
    assert last_threshold_bracket([1,2],[0,3],2)[2]=='right-censored'
    assert last_threshold_bracket([1,2],[0,1],2)[2]=='no sampled exceedance'

@pytest.mark.parametrize('alpha',[1.,0.,2.,3.])
def test_pareto_domain(alpha):
    with pytest.raises(ValueError):centered_pareto(np.random.default_rng(0),10,alpha)

def test_wind_after_town():
    assert np.allclose(triangular_wind(0,[-1,0,5,10,15,20,21]),[3,3,5.5,8,5.5,3,3])

def test_stochastic_docking_deterministic_limit():
    result=docking_trial(np.random.default_rng(0),acceleration_sd=0,adjustment_sd=0,cycle_error_sd=0)
    assert result[3] and result[2]==0 and result[0]%15==0
    stopped=docking_trial(np.random.default_rng(0),max_steps=1)
    assert stopped[3] is False
    assert docking_trial(np.random.default_rng(0),initial_velocity=0)[0]==0

@pytest.mark.parametrize('phi',[0.,.2,.7,1.,1.2])
def test_forecast_variance(phi):
    result=ar1_forecast(1,.01,phi,5,38,11,.3)
    expected=[.09*np.sum(phi**(2*np.arange(h))) for h in range(1,12)]
    assert np.allclose(result.innovation_variance,expected)
    assert result.t.tolist()==list(range(38,49))
    assert np.all(result.lower<=result.forecast) and np.all(result.upper>=result.forecast)

def test_deadtime_and_invalid_inputs():
    assert corrected_deadtime_rate(100,2,.01)==100
    with pytest.raises(ValueError):corrected_deadtime_rate(100,1,.01)
    with pytest.raises(ValueError):wilson_interval(.5,10)
    with pytest.raises(ValueError):ar1_forecast(0,0,.5,1,2,0,.1)
