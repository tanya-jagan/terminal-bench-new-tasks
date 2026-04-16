Easy Task: License Key Reverse Engineering

Prompt: Reverse engineer /app/licensechecker inside the provided environment. Determine a valid license key for username tb3testuser. Write the result to /app/solution.txt and verify using /app/test_solution.py.

Build and run the container:
 - docker build -t license-task .
 - docker run -it license-task

A license key has the form: XXXXX-XXXXX-XXXXX-XXXXX where each X is an uppercase letter or digit (base-36 character set).

Validation steps:
1. Strip dashes. Concatenate the four groups into a 20-character string S.
2. Compute a username hash H:
    H = 0
    for each character c in username:
      H = (H * 31 + c) & 0xFFFFFFFF
3. Decode S as a base-36 number into a 64-bit integer K.
    (characters: 0-9 -> 0-9, A-Z -> 10-35)
4. Extract fields from K:
    version   = (K >> 60) & 0xF         
    checksum  = (K >> 48) & 0xFFF        
    user_hash = (K >> 16) & 0xFFFFFFFF   
    serial    = K & 0xFFFF               
5. Validate:
    - version == 3
    - user_hash == H  (username hash from step 2)
    - checksum == ( (H ^ serial ^ 0xA5F3) * 0x9E37 ) & 0xFFF
    - serial is not zero

If all checks pass: print "License valid." and exit 0.
Otherwise: print "License invalid." and exit 1.

Codex Performance: Codex easily solved this task in ~3 min by reverse engineering the validation logic of licensechecker, identifying the bit-level structure of the license key, deriving the constraints on each field, constructing a valid key, and verifying correctness with the given test. Codex was expected to succeed on this task given that it involves clear computational structure, constraint-solving over small search spaces, and aligns with open0source CTF challenges. The task could be made more difficult with less deterministic logic, a bigger search space, and environmental restrictions, as LLMs are weaker at reverse engineering in less structured problems.