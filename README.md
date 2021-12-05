# dmv_test
Data analysis of DMV Tests for potential fraud.

Around 11/2/21 DMV suspected there was cheating on the driving test web site. The tests were completed more rapidly than thought reasonable. Work started to see if Splunk could detect the fraud. It was hoped that methods could be developed that would be useful for other applications.

The contractor, applus, extracted data from the database and supplied a spreadsheet of 4561 web tests from 10/28/2021 04:30 - 11/5/2021 12:58

## dmv_tests.ipynb
1. Input and clean the raw data with pre_dmv_sample()
    - Eliminate 110 events with result=NaN
    - Eliminate 36 events with more than one ip address
    - Add column ip by split'ing it from IPAdress column
    - Add column result_std by putting None whenevr Result is NaN
    - Add column duration (in minutes) from column TotalTimeSpent/60
    - Write clean_sample_data.csv after raw data is cleaned (optional)
1. plt_duration()
    - histogram of test duration by test result
    - cumulative of same
2. displot_duration()
    - Same as plt_duration but using displot instead of hist
    - Shows kde
1. displot_kde_duration_all()
    - kde plot of all test results
1. displot_kde_duration()
    - shows pass and fail superimposed. Passed exams have two peaks at 12 and 24 minutes. Failed do not.
1. displot_kde_passed_partitions()
    - As above but shows quartiles
1. displot_suspect()
    - Histogram highlights those suspected since thier time taken < 12 min
1. displot_2suspect()
    - Contour plots of duration (<= 12m and > 12m) vs TotalQuestions Answered.
    - Shows that for tests answered in <= 15m the number of questions answered correctly is NOT uniformly spread between 40 and 50 as it is for test duration>15m. 
1. displot_xy(TotalQuestionsCorrect, duration)
    - Same as above but use heat map 
    - Show distribution becoming more uniform and test duration increases
    - Successes start as arly as 3 minutes
    - High number of successes seem to start at 6m and fall off at 10 minutes when the success drops from 44-50 correct to 41-45. 
1. displot_TotalQuestionsCorect, LocalId)
    - Tries to detect a geographic indicator. Not comlete since it treats Localid as a number instead of a factor. Maybe using the name of the Localid will work automatically.
1. displot_xy(TotalQuestionsCorrect, Height)
    - Test whether the success rate depends on hight of applicant.
    - For duration > 12min majority of answers are between 64 and 69 inches. This matches the [avg height of women in NY](https://colonelheight.com/average-height-in-new-york-men-and-women/), 64" and 69" 
    - For "suspects", duration <= 12m, a similar distribution of heights at 63" and 68" is hinted. 
    - The distribution of TotalQuestionsCorrect is definitely different. The number is skewed to higher results, especially for the perfect score of 50.
1. ips_that_are_duplicated()
    - 645 tests used the same ip address as another test
1. displot("of the tests that used duplcate ip address", TotalQuestionsCorrect, duration)
-  


## mywhois.ipynb
1. class Risk() create and use a memoized arin database
    - open the db and load risk dictionary in memory
    - find_arin(ip) find risk and arin info with api's only as needed
1. get_risk(ip) get risk using scamalytics api
1. get_arin(ip) get arin information for the registered netblocks
2. class Debug() write stderr messages

## splunk_search.ipynp
Explore splunk api to search splunk indexes

## pattern.py
class Pattern makes regular expressions easier to use

## clean_test_data.csv
List of unique ip addresses from clean sample data

## Illicit_driver_permits_alleged_Albany_Times_Union_11_14_2021.pdf
Times Union article about the suspected test fraud on DMV web site
