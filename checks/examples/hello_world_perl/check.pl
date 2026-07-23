#!/usr/bin/env perl

use strict;
use warnings;
use Getopt::Long qw(GetOptions);
use JSON qw(encode_json);
use POSIX qw(strftime);
use Sys::Hostname qw(hostname);

my $parameter_a;
GetOptions("ParameterA=s" => \$parameter_a)
    or die "Unable to parse command-line parameters\n";
die "--ParameterA is required\n" unless defined $parameter_a;

my $response = {
    schema_version => "1.0",
    execution => {
        execution_id => join("-", time(), $$, int(rand(1000000))),
        timestamp => strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()),
        hostname => hostname(),
        environment => "EXAMPLE",
        collector_version => "1.0.0",
    },
    results => [
        {
            resource_id => "PerlExample",
            status => "PASS",
            compliance_state => "COMPLIANT",
            severity => "INFO",
            score => 100,
            summary => "Perl example check completed successfully",
            metrics => { result_count => 1 },
            facts => {
                parameter_a => $parameter_a,
                variable_a => $ENV{"VariableA"},
                language => "perl",
            },
            findings => [],
            remediation => undef,
        }
    ],
};

print encode_json($response), "\n";
