CREATE        VIEW [Reporting].[V_CCHP_PregnantMembers_PBI] AS
	select
			pat.PAT_ID
		,	pat.PAT_FIRST_NAME
		,	pat.PAT_LAST_NAME
		,	pat.PAT_MRN_ID
		,	pat.BIRTH_DATE
		,	pat4.PAT_LIVING_STAT_C
		,	IIF(lang.[NAME] = 'Unknown', 'English',lang.[NAME]) "PAT_LANGUAGE"
        ,	mem.MEM_NUMBER
        ,	cvg.SUBSCR_NAME
		,	COALESCE(cvg.SUBSCR_PHONE, hhsc.CARR_ADDR_HM_PHONE, pat.HOME_PHONE) "SUBSCR_PHONE"
		,	[Age] = (CONVERT(int,CONVERT(char(8),SYSDATETIME(),112))-CONVERT(char(8),pat.BIRTH_DATE,112))/10000 
        ,	[PROGRAM] = 
				case
					when pgbp.PLAN_LOB_ID = '16401' THEN '01'
					when pgbp.PLAN_LOB_ID = '16403' THEN '04'
					when pgbp.PLAN_LOB_ID = '16402' THEN '05'
					else NULL
                end
		,	[LOB] =
				case
					when pgbp.PLAN_LOB_ID = '16401' THEN 'STAR'
					when pgbp.PLAN_LOB_ID = '16402' THEN 'CHIP'
					when pgbp.PLAN_LOB_ID = '16403' THEN 'STAR KIDS'
					else NULL
                end			
         ,	mem.MEM_EFF_FROM_DATE
         ,	mem.MEM_EFF_TO_DATE
		 ,	[COUNTY_C] = COALESCE(cvg.SUBSCR_COUNTY_C, hhsc.CARR_ADDR_COUNTY_C, pat.COUNTY_C)
		 ,	[COUNTY_NAME] = ct.NAME
	from 
		Clarity.dbo.COVERAGE_MEMBER_LIST mem
        join Clarity.dbo.PATIENT pat 
			on mem.PAT_ID = PAT.PAT_ID
		join Clarity.dbo.PATIENT_4 pat4
			on pat.PAT_ID = pat4.PAT_ID
		join Clarity.dbo.PAT_ACTIVE_REG reg
			on mem.PAT_ID = reg.PAT_ID
			and reg.REGISTRY_ID = '210502816' --HP HP BABY STEPS REGISTRY
        join Clarity.dbo.COVERAGE cvg 
			on cvg.COVERAGE_ID = mem.COVERAGE_ID
			and cvg.COVERAGE_TYPE_C = 2 -- Managed care 
			and mem.MEM_COVERED_YN = 'Y'
		join Clarity.dbo.PLAN_GRP_BEN_PLAN pgbp
			on pgbp.PLAN_GRP_ID = CVG.PLAN_GRP_ID
            and (pgbp.BEN_PLAN_TERM_DT >= mem.MEM_EFF_FROM_DATE OR pgbp.BEN_PLAN_TERM_DT IS NULL)
            and (pgbp.BEN_PLAN_EFF_DATE <= mem.MEM_EFF_FROM_DATE)
		left join Clarity.dbo.PAT_PER_CARR_ADDR hhsc
			on mem.PAT_ID = hhsc.PAT_ID
			and hhsc.LINE = 1
			and hhsc.CARRIER_ID = '164000000' -- TX HHSC
		left join Clarity.dbo.ZC_COUNTY ct
			on ct.COUNTY_C = hhsc.CARR_ADDR_COUNTY_C
		left join Clarity.dbo.ZC_LANGUAGE lang
			on pat.LANGUAGE_C = lang.LANGUAGE_C

	where
		0 = 0
		and (CONVERT(int,CONVERT(char(8),SYSDATETIME(),112))-CONVERT(char(8),pat.BIRTH_DATE,112))/10000 >= 12
		and mem.MEM_EFF_FROM_DATE <= SYSDATETIME()
		and (mem.MEM_EFF_TO_DATE >= SYSDATETIME() OR mem.MEM_EFF_TO_DATE IS NULL)

;
