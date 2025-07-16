close all;

% Prompt user to select one or more CSV files
[fileNames, pathName] = uigetfile('*.csv', 'Select CSV file(s)', 'MultiSelect', 'on');

% Ensure fileNames is a cell array for consistency
if ischar(fileNames)
    fileNames = {fileNames};
end

% Create output folder if it doesn't exist
outputDir = fullfile(pathName, 'Separated_Trials');
if ~exist(outputDir, 'dir')
    mkdir(outputDir);
end

% Loop through each selected file
for fileIdx = 1:length(fileNames)
    fullFilePath = fullfile(pathName, fileNames{fileIdx});
    forceSig= readmatrix(fullFilePath);

    time = linspace(0,length(forceSig)/10,length(forceSig));

    figure;
    plot(time,forceSig);
    legend('Sensor 1','Sensor 2');
    xlabel('Time(s)');
    ylabel('Amplitude');
    title(fileNames(fileIdx));
    hold on;
    
    % Split data based on baseline min before object grasp
    beforeGraspTime = 3;
    base_samples = beforeGraspTime *10;
    baseSig1 = mean(forceSig(1:base_samples,1));
    baseSig2 = mean(forceSig(1:base_samples,2));

    baseSig = max(baseSig1,baseSig2);
    
    if baseSig <10
        baseSig = 50;
    elseif baseSig < 50
        baseSig = baseSig*3; % minimum in case of baseline zero
    end

    if baseSig1 > baseSig2
        sensor_base = 1;
    else
        sensor_base = 2;
    end

    hold on;
    yline(baseSig, '--b');

    trialStart = 1;
    trialCount = 1;
    i = beforeGraspTime + 1;

    n = size(forceSig,1);
    minReturnLength = 10; 
    buffer = 4; % 0.4 second of buffer 

    trialEnd = 1; %initialized trial start
    grasping = false;  % Start in "not grasping" state

    while i <= n - minReturnLength
        currentVal = forceSig(i, sensor_base);
    
        if ~grasping
            % Look for rise above baseline (start of grasp)
            if currentVal > baseSig
                grasping = true;  % Now we're in a grasp
                trialStart = trialEnd+1;
            end
            i = i + 1;
    
        else
            % If in grasp, look for signal returning below baseline for long enough
            if all(forceSig(i:i+minReturnLength-1, sensor_base) < baseSig)
                trialEnd = min(i + minReturnLength - 1 + buffer, n);
                

                % Extract and save trial
                trialData = forceSig(trialStart:trialEnd, :);
                trialFileName = sprintf('%s_trial_%d.csv', erase(fileNames{fileIdx}, '.csv'),trialCount);
                writematrix(trialData, fullfile(outputDir, trialFileName));
    
                % Plot vertical line at trial end
                xline(trialStart / 10, '--g');
                xline(trialEnd / 10, ':r');
                   
                % Update for next trial
                trialCount = trialCount + 1;
                i = trialEnd + 1;
                grasping = false;  % Wait for next grasp
            else
                i = i + 1;
            end
        end
    end
end 
