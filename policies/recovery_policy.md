\# Revenue Recovery Policy



Version: 1.0

Status: Active



\## Purpose



This policy defines how failed payment transactions should be evaluated

and which recovery strategy should be selected.



\## Recovery Priority



The recovery system should attempt to recover revenue using the least

disruptive viable action before escalating to manual intervention.



Recovery actions are ordered as follows:



1\. Delayed retry

2\. Alternative payment method

3\. Payment method update

4\. Manual review



The selected action must consider the failure reason, payment method,

transaction amount, recoverability, previous recovery attempts, and

customer context.



\## Bank Declined Payments



A bank-declined payment is generally considered recoverable when there is

no evidence of a permanent payment restriction.



For a recoverable bank decline, an alternative payment method may be

offered when an immediate retry is unlikely to succeed.



The recovery system should avoid repeatedly retrying a payment that has

already been declined by the issuing bank.



\## High-Value Transactions



Transactions above ₹10,000 should receive additional scrutiny before

automated recovery.



If the transaction has unusual risk indicators or repeated failures,

manual review may be preferred over automated recovery.



\## Recovery Limits



The system must not create unlimited recovery attempts for the same

transaction.



Each recovery attempt must be recorded and associated with the original

transaction.



\## Recovery Outcome



A recovery case may only be marked as recovered after the payment provider

confirms that the recovery payment has been successfully captured.



Creating a payment link alone does not constitute successful recovery.



\## Auditability



Every recovery decision should record:



\- transaction identifier

\- failure classification

\- selected recovery action

\- decision reasoning

\- policy version used

\- recovery outcome



The system should be able to explain why a recovery action was selected.

