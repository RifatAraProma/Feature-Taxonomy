// Overlay visualizations for all 12 feature types
// Using Hot Pink (#FF1493) for distinctive feature highlighting

export const overlayExtrema = (dataName='extrema', color='#FF1493', seriesType='original') => ([{
  data: {name: dataName},
  mark: {type:'point', filled:true, size:80},
  encoding: {
    x: {field:'t', type:'quantitative'},
    y: {field:'y', type:'quantitative'},
    color: {value: color},
    shape: {
      field:'type', 
      type:'nominal', 
      scale:{domain:['max','min'], range:['triangle-up','triangle-down']},
      legend: null
    },
    tooltip: [
      {field:'type'},
      {field:'t'},
      {field:'y'},
      {field:'series', title:'Series'}
    ]
  }
}]);

export const overlayChangePoints = (dataName='changePoints', color='#FF1493', seriesType='original') => ([
  {
    data: {name: dataName},
    mark: {type:'rule', strokeWidth: 2.5, strokeDash: [8, 4]},
    encoding: {
      x: {field:'t', type:'quantitative'},
      y: {field:'yMin', type:'quantitative'},
      y2: {field:'yMax'},
      color: {value: color},
      opacity: {value:0.7},
      tooltip: [
        {field:'t', title:'Change Point Index'},
        {field:'series', title:'Series'}
      ]
    }
  }
]);

export const overlayRegimes = (dataName='regimes', color='#FF1493', seriesType='original') => {
  // Regimes shown as shaded rectangles
  return [{
    data: {name: dataName},
    mark: {type:'rect', opacity: 0.2},
    encoding: {
      x: {field:'a', type:'quantitative'},
      x2: {field:'b', type:'quantitative'},
      y: {field:'baselineMin', type:'quantitative'},
      y2: {field:'baselineMax', type:'quantitative'},
      color: {value: color},
      tooltip: [
        {field:'a'},
        {field:'b'},
        {field:'baseline'},
        {field:'series', title:'Series'}
      ]
    }
  }];
};

// Combined regimes and change points overlay (like the standalone visualization)
export const overlayRegimesAndChangePoints = (regimesDataName='regimes', cpDataName='changePoints', baselineDataName='regimeBaselines') => {
  return [
    // 1. Shaded regime regions (light background)
    {
      data: {name: regimesDataName},
      mark: {type:'rect', opacity: 0.1},
      encoding: {
        x: {field:'a', type:'quantitative'},
        x2: {field:'b', type:'quantitative'},
        y: {field:'yMin', type:'quantitative'},
        y2: {field:'yMax', type:'quantitative'},
        color: {field:'regimeIndex', type:'nominal', legend: null},
        tooltip: [
          {field:'regimeIndex', title:'Regime'},
          {field:'a', title:'Start'},
          {field:'b', title:'End'},
          {field:'baseline', title:'Mean', format:'.2f'}
        ]
      }
    },
    // 2. Regime baseline lines (horizontal lines showing mean)
    {
      data: {name: baselineDataName},
      mark: {type:'rule', strokeWidth: 3, opacity: 0.8},
      encoding: {
        x: {field:'x1', type:'quantitative'},
        x2: {field:'x2', type:'quantitative'},
        y: {field:'baseline', type:'quantitative'},
        color: {field:'regimeIndex', type:'nominal', legend: null},
        tooltip: [
          {field:'regimeIndex', title:'Regime'},
          {field:'baseline', title:'Mean', format:'.2f'}
        ]
      }
    },
    // 3. Change point markers (vertical dashed lines)
    {
      data: {name: cpDataName},
      mark: {type:'rule', strokeWidth: 2, strokeDash: [4, 4], color: '#dc3545', opacity: 0.7},
      encoding: {
        x: {field:'t', type:'quantitative'},
        y: {field:'yMin', type:'quantitative'},
        y2: {field:'yMax', type:'quantitative'},
        tooltip: [{field:'t', title:'Change Point'}]
      }
    },
    // 4. Change point markers at top (triangles)
    {
      data: {name: cpDataName},
      mark: {type:'point', filled:true, size:120, shape:'triangle-down', color: '#dc3545'},
      encoding: {
        x: {field:'t', type:'quantitative'},
        y: {field:'markerY', type:'quantitative'},
        tooltip: [{field:'t', title:'Change Point'}]
      }
    }
  ];
};

export const overlaySpikes = (dataName='spikesDips', color='#FF1493', seriesType='original') => ([{
  data: {name: dataName},
  mark: {type:'point', filled:true, size:120},
  encoding: {
    x: {field:'t', type:'quantitative'},
    y: {field:'y', type:'quantitative'},
    color: {value: color},
    shape: {
      field: 'type',
      type: 'nominal',
      scale: {domain: ['spike', 'dip'], range: ['circle', 'cross']},
      legend: null
    },
    opacity: {value:0.85},
    tooltip: [
      {field:'type', title:'Outlier Type'},
      {field:'t', title:'Index'},
      {field:'y', title:'Value'},
      {field:'series', title:'Series'}
    ]
  }
}]);

export const overlayTrend = (dataName='trend', color='#FF1493', seriesType='original') => ([{
  data: {name: dataName},
  mark: {type:'line', strokeWidth: 3, strokeDash: [8, 4]},
  encoding: {
    x: {field:'t', type:'quantitative'},
    y: {field:'value', type:'quantitative'},
    color: {value: color},
    opacity: {value:0.8},
    tooltip: [
      {field:'t'},
      {field:'value', format:'.2f'},
      {field:'series', title:'Series'}
    ]
  }
}]);

export const overlayNoise = (dataName='noise', color='#FF1493', seriesType='original') => ([{
  data: {name: dataName},
  mark: {type:'line', strokeWidth: 1.5, interpolate: 'linear'},
  encoding: {
    x: {field:'t', type:'quantitative'},
    y: {field:'value', type:'quantitative'},
    color: {value: color},
    opacity: {value:0.5},
    tooltip: [
      {field:'t'},
      {field:'value', format:'.3f'},
      {field:'series', title:'Series'}
    ]
  }
}]);

export const overlaySlope = (dataName='slope', color='#FF1493', seriesType='original') => {
  return [{
    data: {name: dataName},
    mark: {type:'line', strokeWidth: 2.5},
    encoding: {
      x: {field:'t', type:'quantitative'},
      y: {field:'value', type:'quantitative'},
      color: {value: color},
      opacity: {value:0.7},
      tooltip: [
        {field:'t'},
        {field:'value', title:'Slope', format:'.3f'},
        {field:'series', title:'Series'}
      ]
    }
  }];
};

export const overlayCurvature = (dataName='curvature', color='#FF1493', seriesType='original') => ([{
  data: {name: dataName},
  mark: {type:'point', filled:true, size:60},
  encoding: {
    x: {field:'t', type:'quantitative'},
    y: {field:'value', type:'quantitative'},
    color: {value: color},
    opacity: {
      field:'value', 
      type:'quantitative',
      scale:{domain:[-0.1, 0.1], range:[0.3, 1.0]}
    },
    tooltip: [
      {field:'t'},
      {field:'value', title:'Curvature', format:'.4f'},
      {field:'series', title:'Series'}
    ]
  }
}]);

export const overlayRegression = (regression: any, color='#9C27B0', seriesType='original') => {
  const {slope, intercept, fitted} = regression;
  
  // Convert fitted values to {t, y} format for line mark
  const data = fitted.map((y: number, i: number) => ({
    t: i,
    y,
    series: seriesType,
    slope,
    intercept
  }));
  
  return [{
    data: {values: data},
    mark: {
      type: 'line',
      strokeWidth: 2,
      strokeDash: [8, 4],
      color: color,
      opacity: 0.7
    },
    encoding: {
      x: {field: 't', type: 'quantitative'},
      y: {field: 'y', type: 'quantitative'},
      tooltip: [
        {field: 'series', title: 'Series'},
        {field: 'slope', title: 'Slope', format: '.4f'},
        {field: 'intercept', title: 'Intercept', format: '.2f'}
      ]
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

// Level - show as filled area from y values down to 0
export const overlayLevel = (dataName='level', color='#FF1493', seriesType='original') => ([{
  data: {name: dataName},
  mark: {type: 'area', opacity: 0.4, line: false},
  encoding: {
    x: {field: 't', type: 'quantitative'},
    y: {field: 'y', type: 'quantitative'},
    y2: {value: 0},
    color: {value: color},
    tooltip: [
      {field: 't', title: 'Time'},
      {field: 'y', title: 'Value'},
      {field: 'series', title: 'Series'}
    ]
  }
}]);

// Mean - horizontal line across entire series
export const overlayMean = (meanValue: number, color='#FF1493', seriesType='original') => ([{
  data: {values: [{y: meanValue, series: seriesType}]},
  mark: {
    type: 'rule',
    strokeWidth: 3,
    strokeDash: [12, 6],
    color: color,
    opacity: 0.8
  },
  encoding: {
    y: {
      field: 'y',
      type: 'quantitative'
    },
    x: {value: 0},      // Start at left edge
    x2: {value: 1000},  // End at right edge (chart width)
    tooltip: [
      {field: 'y', title: 'Mean', format: '.2f'},
      {field: 'series', title: 'Series'}
    ]
  }
}]);

// Periodicity - show dominant frequency as annotation (text overlay)
export const overlayPeriodicity = (dataName='periodicity', color='#FF1493', seriesType='original') => ([{
  data: {name: dataName},
  mark: {
    type: 'line',
    strokeWidth: 2.5,
    strokeDash: [6, 3],
    interpolate: 'monotone'
  },
  encoding: {
    x: {field: 't', type: 'quantitative'},
    y: {field: 'value', type: 'quantitative'},
    color: {value: color},
    opacity: {value: 0.7},
    tooltip: [
      {field: 't', title: 't'},
      {field: 'value', title: 'Periodic Component', format: '.3f'},
      {field: 'series', title: 'Series'}
    ]
  }
}]);

// Roughness - show as text annotation on chart
export const overlayRoughness = (roughnessValue: number, color='#FF1493', seriesType='original') => {
  // Position simplified text below original to avoid overlap
  const yOffset = seriesType === 'original' ? 5 : 25;
  
  return [{
    data: {values: [{
      text: `Roughness (${seriesType}): ${roughnessValue.toFixed(4)}`,
      series: seriesType,
      x: 1,  // Use first time point
      y: 0   // Will be positioned at top
    }]},
    mark: {
      type: 'text',
      align: 'left',
      baseline: 'top',
      dx: 5,   // Small offset from left edge
      dy: yOffset,   // Offset from top (different for each series)
      fontSize: 14,
      fontWeight: 'bold',
      color: color
    },
    encoding: {
      x: {field: 'x', type: 'quantitative', axis: null},
      y: {value: 0},  // Position at top of chart
      text: {field: 'text', type: 'nominal'}
    }
  }];
};
