// Overlay visualizations for all 12 feature types
// Using Hot Pink (#FF1493) for distinctive feature highlighting

export const overlayExtrema = (dataName='extrema') => ([{
  data: {name: dataName},
  mark: {type:'point', filled:true, size:80},
  encoding: {
    x: {field:'t', type:'quantitative'},
    y: {field:'y', type:'quantitative'},
    color: {field:'type', type:'nominal', scale:{domain:['max','min'], range:['#FF1493','#FF69B4']}, legend:{title:'Extrema'}},
    tooltip: [{field:'type'},{field:'t'},{field:'y'}]
  }
}]);

export const overlayChangePoints = (dataName='changePoints') => ([{
  data: {name: dataName},
  mark: {type:'rule', strokeWidth: 3},
  encoding: {
    x: {field:'t', type:'quantitative'},
    color: {value:'#FF1493'}, 
    opacity: {value:0.8},
    tooltip: [{field:'t'},{field:'fromBaseline'},{field:'toBaseline'}]
  }
}]);

export const overlayRegimes = (dataName='regimes') => {
  // Regimes shown as shaded rectangles
  return [{
    data: {name: dataName},
    mark: {type:'rect', opacity: 0.2},
    encoding: {
      x: {field:'a', type:'quantitative'},
      x2: {field:'b', type:'quantitative'},
      y: {field:'baselineMin', type:'quantitative'},
      y2: {field:'baselineMax', type:'quantitative'},
      color: {value:'#FF1493'},
      tooltip: [{field:'a'},{field:'b'},{field:'baseline'}]
    }
  }];
};

export const overlaySpikes = (dataName='spikesDips') => ([{
  data: {name: dataName},
  mark: {type:'point', filled:true, size:100, shape:'diamond'},
  encoding: {
    x: {field:'t', type:'quantitative'},
    y: {field:'y', type:'quantitative'},
    color: {value:'#FF1493'},
    opacity: {value:0.9},
    tooltip: [{field:'t'},{field:'y'},{field:'z', title:'Z-score'}]
  }
}]);

export const overlayTrend = (dataName='trend') => ([{
  data: {name: dataName},
  mark: {type:'line', strokeWidth: 3, strokeDash: [8, 4]},
  encoding: {
    x: {field:'t', type:'quantitative'},
    y: {field:'value', type:'quantitative'},
    color: {value:'#FF1493'},
    opacity: {value:0.8}
  }
}]);

export const overlayNoise = (dataName='noise') => ([{
  data: {name: dataName},
  mark: {type:'line', strokeWidth: 1.5, interpolate: 'linear'},
  encoding: {
    x: {field:'t', type:'quantitative'},
    y: {field:'value', type:'quantitative'},
    color: {value:'#FF1493'},
    opacity: {value:0.5}
  }
}]);

export const overlaySlope = (dataName='slope') => {
  return [{
    data: {name: dataName},
    mark: {type:'line', strokeWidth: 2.5},
    encoding: {
      x: {field:'t', type:'quantitative'},
      y: {field:'value', type:'quantitative'},
      color: {value:'#FF1493'},
      opacity: {value:0.7}
    }
  }];
};

export const overlayCurvature = (dataName='curvature') => ([{
  data: {name: dataName},
  mark: {type:'point', filled:true, size:60},
  encoding: {
    x: {field:'t', type:'quantitative'},
    y: {field:'value', type:'quantitative'},
    color: {value:'#FF1493'},
    opacity: {
      field:'value', 
      type:'quantitative',
      scale:{domain:[-0.1, 0.1], range:[0.3, 1.0]}
    },
    tooltip: [{field:'t'},{field:'value', title:'Curvature', format:'.4f'}]
  }
}]);

export const overlayRegression = (origData: any[], alpha: number, beta: number) => {
  // Create regression line points
  const minT = origData.length > 0 ? Math.min(...origData.map(d => d.t)) : 1;
  const maxT = origData.length > 0 ? Math.max(...origData.map(d => d.t)) : 100;
  
  return [{
    data: {
      values: [
        {t: minT, y: alpha + beta * minT},
        {t: maxT, y: alpha + beta * maxT}
      ]
    },
    mark: {type:'line', strokeWidth: 2.5, strokeDash: [10, 5]},
    encoding: {
      x: {field:'t', type:'quantitative'},
      y: {field:'y', type:'quantitative'},
      color: {value:'#FF1493'},
      opacity: {value:0.8}
    }
  }];
};

// Helper to prepare data for Vega-Lite from feature objects
export const prepareFeatureData = (features: any, origData: any[]) => {
  const datasets: any = {};
  
  // Extrema - already in correct format
  if (features.extrema) {
    datasets.extrema = features.extrema;
  }
  
  // Change Points - already in correct format
  if (features.changePoints) {
    datasets.changePoints = features.changePoints;
  }
  
  // Regimes - add baseline range for rect visualization
  if (features.regimes) {
    datasets.regimes = features.regimes.map((r: any) => ({
      ...r,
      baselineMin: r.baseline - 0.5,  // Arbitrary visual height
      baselineMax: r.baseline + 0.5
    }));
  }
  
  // Spikes/Dips - already in correct format
  if (features.spikesDips) {
    datasets.spikesDips = features.spikesDips;
  }
  
  // Trend - convert to {t, value} format
  if (features.trend && features.trend.values) {
    datasets.trend = features.trend.values.map((v: number, i: number) => ({
      t: i + 1,
      value: v
    }));
  }
  
  // Noise - convert to {t, value} format
  if (features.noise && features.noise.values) {
    datasets.noise = features.noise.values.map((v: number, i: number) => ({
      t: i + 1,
      value: v
    }));
  }
  
  // Slope - already has index and values
  if (features.slope && features.slope.values) {
    datasets.slope = features.slope.values.map((v: number, i: number) => ({
      t: features.slope.index[i] || i + 1,
      value: v
    }));
  }
  
  // Curvature - already has index and values
  if (features.curvature && features.curvature.values) {
    datasets.curvature = features.curvature.values.map((v: number, i: number) => ({
      t: features.curvature.index[i] || i + 2,
      value: v
    }));
  }
  
  return datasets;
};

// Level - show as horizontal line across interval
export const overlayLevel = (dataName='level') => ([{
  data: {name: dataName},
  mark: {type: 'rule', color: '#FF1493', strokeWidth: 3, strokeDash: [8, 4]},
  encoding: {
    x: {field: 'a', type: 'quantitative'},
    x2: {field: 'b'},
    y: {field: 'value', type: 'quantitative'},
    opacity: {value: 0.8}
  }
}]);

// Mean - horizontal line across entire series
export const overlayMean = (meanValue: number) => ([{
  data: {values: [{y: meanValue}]},
  mark: {type: 'rule', color: '#FF1493', strokeWidth: 3, strokeDash: [12, 6]},
  encoding: {
    y: {field: 'y', type: 'quantitative'},
    opacity: {value: 0.8}
  }
}]);

// Periodicity - show dominant frequency as annotation (text overlay)
export const overlayPeriodicity = (period: number, dominantFreq: number) => ([{
  data: {values: [{text: `Period: ${period.toFixed(1)} | Freq: ${dominantFreq.toFixed(3)}`}]},
  mark: {
    type: 'text',
    align: 'right',
    baseline: 'top',
    dx: -10,
    dy: 10,
    fontSize: 16,
    fontWeight: 700,
    color: '#FF1493'
  },
  encoding: {
    text: {field: 'text', type: 'nominal'}
  }
}]);

// Roughness - show as text annotation
export const overlayRoughness = (roughnessValue: number) => {
  return [{
    data: {values: [{annotation: `Roughness: ${roughnessValue.toFixed(4)}`}]},
    mark: {
      type: 'text',
      align: 'left',
      baseline: 'top',
      dx: 10,
      dy: 10,
      fontSize: 16,
      fontWeight: 700,
      color: '#FF1493',
      opacity: 1.0
    },
    encoding: {
      text: {field: 'annotation', type: 'nominal'}
    }
  }];
};
