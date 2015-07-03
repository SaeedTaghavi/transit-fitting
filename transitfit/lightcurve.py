from __future__ import print_function, division

import numpy as np
from numpy import ma
import pandas as pd
import matplotlib.pyplot as plt

from transit import Central, System, Body

from .utils import t_folded, lc_eval



class Planet(object):
    def __init__(self, period, epoch, duration):
        self.period = period
        self.epoch = epoch
        self.duration = duration
        self.lc = None

    def t_folded(self, t):
        return t_folded(t, self.period, self.epoch)

    def t_close(self, t, width=2):
        return np.absolute(self.t_folded(t)) < width*self.duration

    def in_transit(self, t, width=0.55):
        return self.t_close(t, width=width)

    def ith_transit(self, t, i, width=2):
        """Returns True around ith transit (as measured from epoch)
        """
        per, ep = (self.period, self.epoch)
        close = np.absolute(((t - ep + per/2) / per) 
                           - per/2 - i ) < width*self.duration
        return close
    
    
class LightCurve(object):
    """Object holding time/flux data and info about transiting planets

    :param time,flux,flux_err:
        Time series data.

    :param texp:
        Exposure time.  If not provided, will be assumed to be median
        of delta-t.
        
    """
    def __init__(self, time, flux, flux_err=0.0001,
                 mask=None, texp=None, planets=None,
                 detrend=True):

        
        if mask is None:
            mask = ~np.isfinite(flux)
        self.mask = np.array(mask).astype(bool)

        if texp is None:
            texp = np.median(time[1:]-time[:-1])
        self.texp = texp
        
        if planets is None:
            planets = []
        self.planets = planets

        self._time = np.array(time)
        self._flux = np.array(flux)
        self._flux_err = np.array(flux_err)

        if detrend:
            self.median_detrend()
        else:
            self._detrended_flux = np.array(flux)
            
    @property
    def t(self):
        return self.time

    @property
    def f(self):
        return self.f
    
    @property
    def time(self):
        return self._time[~self.mask]
    
    @property
    def rawflux(self):
        return self._flux[~self.mask]
        
    @property
    def flux_err(self):
        return self._flux_err[~self.mask]
        
    @property
    def flux(self):
        return self._detrended_flux[~self.mask]

    def median_detrend(self, window=75):
        f = self._flux.copy()
        f[self.any_intransit] = np.nan
        f_median = pd.rolling_median(f, 75, center=True,
                                     min_periods=1)
        self._detrended_flux = self._flux / f_median

    @property
    def n_planets(self):
        return len(self.planets)
        
    def add_planet(self, planet):
        planet.lc = self
        self.planets.append(planet)

    def t_folded(self, i=0):
        """Times folded on the period and epoch of planet i
        """
        return self.planets[i].t_folded(self.time)

    def t_close(self, i=0, width=2):
        """Boolean array with True everywhere within width*duration of planet i 
        """
        return self.planets[i].t_close(self.time, width=width)

    @property
    def anyclose(self):
        close = np.zeros_like(self.time).astype(bool)
        for i in range(self.n_planets):
            close += self.t_close(i)
        return close

    def intransit(self, i=0, width=0.55):
        """Boolean mask True everywhere within 0.6*duration of planet i
        """
        return self.planets[i].in_transit(self.time, width=width)

    @property
    def any_intransit(self):
        intrans = np.zeros_like(self.time).astype(bool)
        for i in range(self.n_planets):
            intrans += self.intransit(i)
        return intrans

    @property
    def n_transits(self):
        tspan = self.time[-1] - self.time[0]
        return [(tspan // p.period) + 1 for p in self.planets]
        
    def ith_transit(self, i, i_planet=0, width=2):
        """returns True around i-th transit for planet number "i_planet"
        """
        return self.planets[i_planet].ith_transit(self.t, i, width=width)

    def transit_stack(self, i=0, width=2):
        """returns a 2-d array of times/fluxes with subsequent transits in each row
        """
        
        
    